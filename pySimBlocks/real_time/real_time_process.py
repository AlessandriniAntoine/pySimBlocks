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

"""RealTimeProcess — base class for soft real-time multiprocessing applications."""

from __future__ import annotations

import multiprocessing
import multiprocessing.sharedctypes
from abc import abstractmethod
from typing import Callable, ClassVar, Dict, List, Optional

import numpy as np


# ---------------------------------------------------------------------------
# @on decorator
# ---------------------------------------------------------------------------

_ON_ATTR = "_rt_on_event"


def on(event: str) -> Callable:
    """Decorator that marks a method as a handler for *event*.

    Only one event per handler is allowed. Use :class:`Gate` to aggregate
    several events into a single synthetic trigger.

    Example::

        @on("measure_ready")
        def handle_measure(self):
            ...
    """
    def decorator(fn: Callable) -> Callable:
        if hasattr(fn, _ON_ATTR):
            raise TypeError(
                f"@on can only be used once per handler. "
                f"Use Gate to wait for multiple events. "
                f"(offending handler: '{fn.__name__}')"
            )
        setattr(fn, _ON_ATTR, event)
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------

class Gate:
    """Aggregates several events into one synthetic trigger.

    When all events in *wait_for* have been received since the last trigger,
    the Gate fires a synthetic event named *trigger*.

    Example::

        gates = [Gate("tick", wait_for=["frame_ready", "measure_ready"])]

        @on("tick")
        def handle_tick(self): ...
    """

    def __init__(self, trigger: str, wait_for: List[str]):
        if not wait_for:
            raise ValueError(f"Gate '{trigger}': wait_for must not be empty.")
        self.trigger  = trigger
        self.wait_for = list(wait_for)
        self._received: Dict[str, bool] = {e: False for e in wait_for}

    def feed(self, event: str) -> bool:
        """Mark *event* as received. Returns True when all events have fired."""
        if event in self._received:
            self._received[event] = True
        return all(self._received.values())

    def reset(self) -> None:
        for k in self._received:
            self._received[k] = False

    @property
    def pending_events(self) -> List[str]:
        return [e for e, received in self._received.items() if not received]


# ---------------------------------------------------------------------------
# dtype helpers
# ---------------------------------------------------------------------------

_DTYPE_SPECS = {
    "f": ("d", np.float64),
    "d": ("d", np.float64),
    "i": ("i", np.int32),
    "l": ("l", np.int64),
    "b": ("b", np.bool_),
    "u": ("I", np.uint32),
}

_DEFAULT_NP_DTYPE = np.float64


def _resolve_dtype(dtype: str):
    """Return (typecode, np_dtype) for a user-supplied dtype string."""
    spec = _DTYPE_SPECS.get(dtype)
    if spec is None:
        raise ValueError(
            f"[shared] Unknown dtype '{dtype}'. "
            f"Supported: {list(_DTYPE_SPECS.keys())}"
        )
    return spec  # (typecode, np_dtype)


# ---------------------------------------------------------------------------
# SharedProxy
# ---------------------------------------------------------------------------

class _SharedProxy:
    """Transparent read/write proxy for shared memory arrays.

    Three access patterns:

    Single field (one lock per call)::

        self.shared.Camera = np.array([...])   # write
        val = self.shared.Camera               # read — returns pre-alloc buffer

    Grouped read — ONE lock for N fields, coherent snapshot::

        s = self.shared.read("Camera", "Ref_cl", "Mode")
        # s["Camera"], s["Ref_cl"], s["Mode"] — all from the same lock window

    Grouped write — ONE lock for N fields::

        self.shared.write(Camera=arr, Ref_cl=ref)

    Pre-allocated read buffers are created the first time each field is read
    inside a given process (after fork). Zero allocation on the hot path.

    Args:
        arrays: Dict name -> ``multiprocessing.Array``
        dtypes: Dict name -> numpy dtype
    """

    def __init__(
        self,
        arrays: Dict[str, "multiprocessing.Array"],
        dtypes: Dict[str, type] | None = None,
    ):
        object.__setattr__(self, "_arrays",  arrays)
        object.__setattr__(self, "_dtypes",  dtypes or {})
        # Pre-allocated read buffers, created lazily per-process after fork.
        # Key: field name  Value: np.ndarray (same dtype, same shape as array)
        object.__setattr__(self, "_buffers", {})

    # ------------------------------------------------------------------
    # Single-field access (one lock per call)
    # ------------------------------------------------------------------

    def __getattr__(self, name: str) -> np.ndarray:
        arrays  = object.__getattribute__(self, "_arrays")
        dtypes  = object.__getattribute__(self, "_dtypes")
        buffers = object.__getattribute__(self, "_buffers")

        if name not in arrays:
            raise AttributeError(
                f"[shared] No shared field '{name}'. "
                f"Available: {list(arrays.keys())}"
            )
        arr      = arrays[name]
        np_dtype = dtypes.get(name, _DEFAULT_NP_DTYPE)

        # --- PRE-ALLOC: create buffer once per process, reuse forever ---
        if name not in buffers:
            buffers[name] = np.empty(len(arr), dtype=np_dtype)
        buf = buffers[name]

        with arr.get_lock():
            np.copyto(buf, arr[:])   # write into pre-allocated buffer, no malloc
        return buf

    def __setattr__(self, name: str, value) -> None:
        arrays = object.__getattribute__(self, "_arrays")
        dtypes = object.__getattribute__(self, "_dtypes")

        if name not in arrays:
            raise AttributeError(
                f"[shared] No shared field '{name}'. "
                f"Available: {list(arrays.keys())}"
            )
        arr      = arrays[name]
        np_dtype = dtypes.get(name, _DEFAULT_NP_DTYPE)
        flat = np.asarray(value, dtype=np_dtype).flatten()
        with arr.get_lock():
            arr[:] = flat

    # ------------------------------------------------------------------
    # Grouped access — single lock window for multiple fields
    # ------------------------------------------------------------------

    def read(self, *names: str) -> Dict[str, np.ndarray]:
        """Read several fields under a single global lock window.

        More efficient and coherent than N separate attribute reads when
        a handler needs multiple fields from the same tick.

        Returns a dict of pre-allocated numpy arrays (same buffers as
        single-field access — no extra allocation).

        Example::

            s = self.shared.read("Camera", "Ref_cl", "Ref_ol", "Mode")
            runner.tick(inputs={
                "Camera": s["Camera"].reshape(-1, 1),
                "Ref_cl": s["Ref_cl"].reshape(-1, 1),
            })
        """
        arrays  = object.__getattribute__(self, "_arrays")
        dtypes  = object.__getattribute__(self, "_dtypes")
        buffers = object.__getattribute__(self, "_buffers")

        for name in names:
            if name not in arrays:
                raise AttributeError(
                    f"[shared] No shared field '{name}'. "
                    f"Available: {list(arrays.keys())}"
                )

        result: Dict[str, np.ndarray] = {}

        # Acquire all locks in deterministic order to avoid deadlocks,
        # then copy all fields, then release all locks.
        ordered = sorted(names)
        locks   = [arrays[n].get_lock() for n in ordered]

        for lock in locks:
            lock.acquire()
        try:
            for name in names:
                arr      = arrays[name]
                np_dtype = dtypes.get(name, _DEFAULT_NP_DTYPE)
                if name not in buffers:
                    buffers[name] = np.empty(len(arr), dtype=np_dtype)
                np.copyto(buffers[name], arr[:])
                result[name] = buffers[name]
        finally:
            for lock in locks:
                lock.release()

        return result

    def write(self, **fields) -> None:
        """Write several fields under a single global lock window.

        Example::

            self.shared.write(Ref_ol=np.array([0.1, 0.2]), Update=np.array([1]))
        """
        arrays = object.__getattribute__(self, "_arrays")
        dtypes = object.__getattribute__(self, "_dtypes")

        for name in fields:
            if name not in arrays:
                raise AttributeError(
                    f"[shared] No shared field '{name}'. "
                    f"Available: {list(arrays.keys())}"
                )

        ordered = sorted(fields.keys())
        locks   = [arrays[n].get_lock() for n in ordered]

        for lock in locks:
            lock.acquire()
        try:
            for name, value in fields.items():
                np_dtype = dtypes.get(name, _DEFAULT_NP_DTYPE)
                arrays[name][:] = np.asarray(value, dtype=np_dtype).flatten()
        finally:
            for lock in locks:
                lock.release()

    def __repr__(self) -> str:
        arrays = object.__getattribute__(self, "_arrays")
        dtypes = object.__getattribute__(self, "_dtypes")
        fields = {k: dtypes.get(k, _DEFAULT_NP_DTYPE).__name__ for k in arrays}
        return f"<SharedProxy {fields}>"


# ---------------------------------------------------------------------------
# RealTimeProcess
# ---------------------------------------------------------------------------

class RealTimeProcess(multiprocessing.Process):
    """Base class for all processes in a soft real-time application.

    Subclasses declare which events they emit and listen to via class
    attributes, and implement :meth:`setup` plus either:

    - :meth:`run` — for producer processes with their own blocking loop.
    - ``@on("event")`` handlers — for reactive processes.
    """

    emits:   ClassVar[List[str]] = []
    listens: ClassVar[List[str]] = []
    gates:   ClassVar[List[Gate]] = []

    shared:        _SharedProxy
    _events_in:    Dict[str, "multiprocessing.Event"]
    _events_out:   Dict[str, List["multiprocessing.Event"]]
    _project_yaml: Optional[str]

    def __init__(self):
        super().__init__(daemon=True)
        self.shared         = _SharedProxy({})
        self._events_in     = {}
        self._events_out    = {}
        self._project_yaml  = None

        # Collect @on handlers at class definition time
        self._handlers: Dict[str, str] = {}  # event -> method name
        for attr_name in dir(type(self)):
            method = getattr(type(self), attr_name, None)
            if callable(method) and hasattr(method, _ON_ATTR):
                event = getattr(method, _ON_ATTR)
                if event in self._handlers:
                    raise TypeError(
                        f"[{type(self).__name__}] Duplicate @on handler for "
                        f"event '{event}'."
                    )
                self._handlers[event] = attr_name

    # ------------------------------------------------------------------
    # API for subclasses
    # ------------------------------------------------------------------

    @abstractmethod
    def setup(self) -> None:
        """Initialise hardware, models, and local state (called once, in child)."""

    def run(self) -> None:
        """Default entry point: setup then reactive dispatch loop."""
        self.setup()
        self._dispatch_loop()

    def emit(self, event: str) -> None:
        """Signal *event* to all connected downstream processes."""
        if event not in self.emits:
            raise KeyError(
                f"[{type(self).__name__}] Undeclared event '{event}'. "
                f"Add it to emits = [...]."
            )
        for mp_event in self._events_out.get(event, []):
            mp_event.set()

    def load_runner(
        self,
        input_blocks: List[str],
        output_blocks: List[str],
        *,
        target_dt: Optional[float] = None,
    ):
        """Build and return an initialised RealTimeRunner from the session yaml.

        Example::

            def setup(self):
                self.runner = self.load_runner(
                    input_blocks=["Camera", "Ref_cl", "Ref_ol", "Mode"],
                    output_blocks=["Cmd"],
                    target_dt=1/60,
                )
        """
        if not self._project_yaml:
            raise RuntimeError(
                f"[{type(self).__name__}] load_runner() called but no "
                "project yaml was set by the session."
            )
        from pySimBlocks.project import load_simulator_from_project
        from pySimBlocks.real_time.real_time_runner import RealTimeRunner

        sim, _ = load_simulator_from_project(self._project_yaml)
        runner = RealTimeRunner(
            sim,
            input_blocks=input_blocks,
            output_blocks=output_blocks,
            target_dt=target_dt,
        )
        runner.initialize()
        return runner

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _dispatch_loop(self) -> None:
        """Reactive loop: block on each event in turn, dispatch on arrival.

        Uses ``wait()`` without timeout — the OS wakes this process the moment
        an event is set, with ~50 µs latency instead of the ~5 ms polling
        latency of ``wait(timeout=0.005)``.
        """
        gate_index: Dict[str, List[Gate]] = {}
        for gate in self.gates:
            for ev in gate.wait_for:
                gate_index.setdefault(ev, []).append(gate)

        while True:
            for event_name, mp_event in self._events_in.items():
                # --- WAIT: block until event arrives, no polling ---
                mp_event.wait()
                mp_event.clear()
                self._handle_event(event_name, gate_index)

    def _handle_event(
        self,
        event_name: str,
        gate_index: Dict[str, List[Gate]],
    ) -> None:
        if event_name in self._handlers:
            getattr(self, self._handlers[event_name])()

        for gate in gate_index.get(event_name, []):
            if gate.feed(event_name):
                gate.reset()
                trigger = gate.trigger
                if trigger in self._handlers:
                    getattr(self, self._handlers[trigger])()
