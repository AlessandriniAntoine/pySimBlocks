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

import logging
import multiprocessing
import multiprocessing.connection
from multiprocessing.sharedctypes import SynchronizedArray
import time
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

from pySimBlocks.real_time.real_time_process import RealTimeProcess, _SharedProxy, _resolve_dtype

logger = logging.getLogger(__name__)


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
        # process id -> shutdown writer pipe end
        self._shutdown_writers: Dict[int, multiprocessing.connection.Connection] = {}

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
        self._wire(shared_arrays, shared_dtypes)

        for p in self._processes:
            p.start()

        logger.info(
            "RealTimeSession: started %d process(es). Press Ctrl-C to stop.",
            len(self._processes),
        )
        try:
            while True:
                time.sleep(1.0)
                for p in self._processes:
                    if not p.is_alive():
                        logger.error(
                            "RealTimeSession: process '%s' (pid=%s) exited "
                            "unexpectedly (exitcode=%s).",
                            type(p).__name__, p.pid, p.exitcode,
                        )
        except KeyboardInterrupt:
            logger.info("RealTimeSession: stopping...")
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
        # Yaml gives us block names with default size=1 as a safety net.
        # declare_shared() overrides both size and dtype.
        io_specs = self._parse_io_specs()
        all_specs = {**io_specs, **self._extra_shared}

        arrays: Dict[str, SynchronizedArray] = {}
        np_dtypes: Dict[str, type] = {}

        for name, size in all_specs.items():
            dtype_str = self._extra_dtypes.get(name, "d")
            typecode, np_dtype = _resolve_dtype(dtype_str)
            arrays[name]    = multiprocessing.Array(typecode, size * [0])
            np_dtypes[name] = np_dtype

        return arrays, np_dtypes

    def _wire(
        self,
        shared_arrays: Dict[str, SynchronizedArray],
        shared_dtypes: Dict[str, type],
    ) -> None:
        """Inject shared proxy, pipes, and shutdown connections into each process."""
        shared_proxy = _SharedProxy(shared_arrays, shared_dtypes)

        # One pipe per (dst_instance, event_name) — all sources for the same
        # (event, dst) pair share the same writer end.
        incoming: Dict[Tuple[int, str], Tuple[
            multiprocessing.connection.Connection,
            multiprocessing.connection.Connection,
        ]] = {}
        for event, src, dst in self._connections:
            key = (id(dst), event)
            if key not in incoming:
                incoming[key] = multiprocessing.Pipe(duplex=False)  # (reader, writer)

        for p in self._processes:
            # Shutdown pipe: session writes, process reads to exit _dispatch_loop.
            shutdown_reader, shutdown_writer = multiprocessing.Pipe(duplex=False)
            self._shutdown_writers[id(p)] = shutdown_writer
            p._shutdown_reader = shutdown_reader

            # events_in: reader end for each event this process receives.
            events_in: Dict[str, multiprocessing.connection.Connection] = {}
            for event, src, dst in self._connections:
                if dst is p:
                    reader, _ = incoming[(id(p), event)]
                    events_in[event] = reader
            p._events_in = events_in

            # events_out: writer ends for each event this process emits.
            events_out: Dict[str, List[multiprocessing.connection.Connection]] = {}
            for event, src, dst in self._connections:
                if src is p:
                    _, writer = incoming[(id(dst), event)]
                    events_out.setdefault(event, []).append(writer)
            p._events_out = events_out

            p.shared        = shared_proxy
            p._project_yaml = self._project_yaml

    def _shutdown(self) -> None:
        """Stop all processes gracefully, falling back to SIGTERM/SIGKILL.

        Sequence:
        1. Send a shutdown byte on each process's shutdown pipe so that
           ``_dispatch_loop`` exits cleanly and ``finally:`` blocks in
           subclass ``run()`` have a chance to release hardware resources.
        2. Wait up to 3 s for each process to exit on its own.
        3. Send SIGTERM to any process that is still alive.
        4. Wait up to 3 s more, then SIGKILL as a last resort.

        .. note::
            Steps 1-2 replace the original ``join(timeout=2) → terminate()``
            pattern (FIX ⑤) so that hardware teardown in ``finally:`` blocks
            (cameras, DAQ boards, serial ports, …) is normally executed before
            any signal is sent.
        """
        # FIX ⑤ — signal processes via the shutdown pipe first so their
        # finally: blocks (hardware teardown) have time to run.
        for _, writer in self._shutdown_writers.items():
            try:
                writer.send_bytes(b"\x00")
            except Exception:
                pass

        # Give processes time to exit cleanly on their own.
        for p in self._processes:
            p.join(timeout=3.0)

        # Escalate to SIGTERM for any stragglers.
        for p in self._processes:
            if p.is_alive():
                logger.warning(
                    "RealTimeSession: process '%s' (pid=%s) did not exit "
                    "within 3 s — sending SIGTERM.",
                    type(p).__name__, p.pid,
                )
                p.terminate()

        for p in self._processes:
            p.join(timeout=3.0)

        # Last resort: SIGKILL.
        for p in self._processes:
            if p.is_alive():
                logger.error(
                    "RealTimeSession: process '%s' (pid=%s) did not respond "
                    "to SIGTERM — sending SIGKILL.",
                    type(p).__name__, p.pid,
                )
                p.kill()

        for p in self._processes:
            p.join(timeout=3.0)

        logger.info("RealTimeSession: all processes stopped.")

    def _parse_io_specs(self) -> Dict[str, int]:
        with open(self._project_yaml, "r") as f:
            cfg = yaml.safe_load(f)
        return {
            block["name"]: int((block.get("parameters") or {}).get("size", 1))
            for block in cfg.get("diagram", {}).get("blocks", [])
            if block.get("type") in {"external_input", "external_output"}
        }
