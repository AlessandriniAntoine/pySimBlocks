# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
# ******************************************************************************
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
#  for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ******************************************************************************
#  Authors: see Authors.txt
# ******************************************************************************

"""RealTimeSession — wiring and launch point for soft real-time applications."""

from __future__ import annotations

import multiprocessing
import time
from pathlib import Path
from typing import Dict, List, Tuple

from pySimBlocks.real_time.real_time_process import RealTimeProcess, _SharedProxy, _resolve_dtype


class RealTimeSession:
    """Wires and launches all processes of a soft real-time application.

    The session:
    - Builds ``multiprocessing.Array`` for every field declared via
      :meth:`declare_shared` (and for ``ExternalInput``/``ExternalOutput``
      blocks found in the yaml as fallback, with size=1).
    - Creates ``multiprocessing.Event`` objects for every event declared
      across all processes.
    - Wires events between processes according to :meth:`connect` calls.
    - Injects ``shared``, ``_events_in``, ``_events_out``, and
      ``_project_yaml`` into each process before starting.

    Args:
        project_yaml: Path to the ``project.yaml`` file.
    """

    def __init__(self, project_yaml: str | Path):
        self._project_yaml = str(Path(project_yaml).resolve())
        self._processes: List[RealTimeProcess] = []
        self._connections: List[Tuple[str, RealTimeProcess, RealTimeProcess]] = []
        # name -> flat size
        self._extra_shared: Dict[str, int] = {}
        # name -> typecode string ("d", "b", "i", ...)
        self._extra_dtypes: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, *processes: RealTimeProcess) -> None:
        """Register one or more process instances with the session."""
        for p in processes:
            self._processes.append(p)

    def declare_shared(self, name: str, size: int, dtype: str = "d") -> None:
        """Declare a shared memory field accessible to all processes.

        Use this for every I/O block whose size differs from the yaml default
        (which is 1), and for any inter-process field not in the diagram
        (e.g. a GUI start flag, a recording flag).

        Args:
            name:  Field name — accessible as ``self.shared.<name>`` in any
                   process.
            size:  Number of elements in the flat array.
            dtype: Element type:

                   - ``"d"`` / ``"f"`` — float64 (default)
                   - ``"i"``           — int32
                   - ``"l"``           — int64
                   - ``"b"``           — bool
                   - ``"u"``           — uint32

        Examples::

            session.declare_shared("Camera", 6)               # 6 float64
            session.declare_shared("Start",  1, dtype="b")    # 1 bool
            session.declare_shared("Mode",   1, dtype="i")    # 1 int32
        """
        self._extra_shared[name] = size
        self._extra_dtypes[name] = dtype

    def connect(
        self,
        event: str,
        src: RealTimeProcess,
        dst: RealTimeProcess,
    ) -> None:
        """Declare that *src* sends *event* to *dst*.

        Args:
            event: Event name (must be in ``src.emits`` and in ``dst.listens``
                   or referenced by a ``dst.gates`` entry).
            src:   Instance of the source process.
            dst:   Instance of the destination process.
        """
        if event not in src.emits:
            raise ValueError(
                f"connect(): event '{event}' is not in "
                f"{type(src).__name__}.emits."
            )
        dst_events = set(dst.listens)
        for gate in dst.gates:
            dst_events.update(gate.wait_for)
        if event not in dst_events:
            raise ValueError(
                f"connect(): event '{event}' is not in "
                f"{type(dst).__name__}.listens "
                f"nor referenced by any of its Gates."
            )
        self._connections.append((event, src, dst))

    def run(self) -> None:
        """Wire everything, start all processes, and block until interrupted."""
        shared_arrays, shared_dtypes = self._build_shared_arrays()
        mp_events = self._build_mp_events()
        self._wire(shared_arrays, shared_dtypes, mp_events)

        for p in self._processes:
            p.start()

        print(f"[RealTimeSession] Started {len(self._processes)} process(es). "
              "Press Ctrl-C to stop.")
        try:
            while True:
                time.sleep(1.0)
                for p in self._processes:
                    if not p.is_alive():
                        print(f"[RealTimeSession] Process '{type(p).__name__}' "
                              f"(pid={p.pid}) exited unexpectedly "
                              f"(exitcode={p.exitcode}).")
        except KeyboardInterrupt:
            print("\n[RealTimeSession] Stopping...")
        finally:
            self._shutdown()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_shared_arrays(self):
        """Build typed shared arrays from yaml + declare_shared declarations.

        Returns:
            Tuple of:
            - Dict  name -> ``multiprocessing.Array``
            - Dict  name -> numpy dtype  (forwarded to the proxy)
        """
        import numpy as np

        # Yaml gives us block names with default size=1 as a safety net.
        # declare_shared() overrides both size and dtype.
        io_specs = _parse_io_specs(self._project_yaml)
        all_specs = {**io_specs, **self._extra_shared}

        arrays: Dict[str, multiprocessing.Array] = {}
        np_dtypes: Dict[str, type] = {}

        for name, size in all_specs.items():
            dtype_str = self._extra_dtypes.get(name, "d")
            typecode, np_dtype = _resolve_dtype(dtype_str)
            arrays[name]    = multiprocessing.Array(typecode, size * [0])
            np_dtypes[name] = np_dtype

        return arrays, np_dtypes

    def _build_mp_events(self) -> Dict[str, multiprocessing.Event]:
        """Create one ``multiprocessing.Event`` per unique event name."""
        names: set[str] = set()
        for p in self._processes:
            names.update(p.emits)
            names.update(p.listens)
            for gate in p.gates:
                names.update(gate.wait_for)
        return {name: multiprocessing.Event() for name in names}

    def _wire(
        self,
        shared_arrays: Dict[str, multiprocessing.Array],
        shared_dtypes: Dict[str, type],
        mp_events: Dict[str, multiprocessing.Event],
    ) -> None:
        """Inject shared proxy and event references into each process."""
        shared_proxy = _SharedProxy(shared_arrays, shared_dtypes)

        # One mp.Event per (dst_instance, event_name).
        incoming: Dict[Tuple[int, str], multiprocessing.Event] = {}
        for event, src, dst in self._connections:
            key = (id(dst), event)
            if key not in incoming:
                incoming[key] = multiprocessing.Event()

        for p in self._processes:
            # events_in: events this process waits on
            events_in: Dict[str, multiprocessing.Event] = {}
            for event, src, dst in self._connections:
                if dst is p:
                    events_in[event] = incoming[(id(p), event)]
            p._events_in = events_in

            # events_out: for each emitted event, list of downstream mp.Events
            events_out: Dict[str, List[multiprocessing.Event]] = {}
            for event, src, dst in self._connections:
                if src is p:
                    events_out.setdefault(event, []).append(
                        incoming[(id(dst), event)]
                    )
            p._events_out = events_out

            p.shared        = shared_proxy
            p._project_yaml = self._project_yaml

    def _shutdown(self) -> None:
        for p in self._processes:
            if p.is_alive():
                p.terminate()
        for p in self._processes:
            p.join(timeout=5.0)
            if p.is_alive():
                p.kill()
        print("[RealTimeSession] All processes stopped.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_io_specs(project_yaml: str) -> Dict[str, int]:
    """Read ExternalInput/Output block names from the yaml (size defaults to 1)."""
    import yaml
    with open(project_yaml, "r") as f:
        cfg = yaml.safe_load(f)
    specs: Dict[str, int] = {}
    for block in cfg.get("diagram", {}).get("blocks", []):
        if block.get("type") in {"external_input", "external_output"}:
            params = block.get("parameters", {}) or {}
            specs[block["name"]] = int(params.get("size", 1))
    return specs
