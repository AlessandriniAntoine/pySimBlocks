"""
Tests for RealTimeProcess, RealTimeSession, and their integration.

Integration tests start real child processes (fork on Linux).
Shared multiprocessing primitives are used as out-of-band result channels
so that no test infrastructure lives inside the child process.
"""
import multiprocessing
import time

import numpy as np
import pytest

from pySimBlocks.real_time.real_time_process import Gate, RealTimeProcess, on
from pySimBlocks.real_time.real_time_session import RealTimeSession, _parse_io_specs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _start_and_stop(processes, *, run_for=0.6):
    """Start all processes, wait run_for seconds, then terminate and join."""
    for p in processes:
        p.start()
    time.sleep(run_for)
    for p in processes:
        if p.is_alive():
            p.terminate()
    for p in processes:
        p.join(timeout=2.0)


def _session(tmp_path, *processes, connections=(), shared=()):
    """Build a wired-but-not-started session from tmp_path/project.yaml."""
    yaml = tmp_path / "project.yaml"
    yaml.write_text("diagram:\n  blocks: []\n")

    session = RealTimeSession(str(yaml))
    for p in processes:
        session.add(p)
    for name, size in shared:
        session.declare_shared(name, size)
    for event, src, dst in connections:
        session.connect(event, src, dst)
    session._wire(*session._build_shared_arrays())
    return session


# ---------------------------------------------------------------------------
# Unit: Gate per-instance isolation
# ---------------------------------------------------------------------------

def test_gates_are_not_shared_between_instances():
    """
    The class-level gates list is deep-copied per instance.
    Feeding a gate on p1 must not affect p2's gate state.
    """
    class MyProcess(RealTimeProcess):
        gates = [Gate("tick", wait_for=["A", "B"])]
        def setup(self): pass

    p1 = MyProcess()
    p2 = MyProcess()

    p1._gates[0].feed("A")

    assert set(p2._gates[0].pending_events) == {"A", "B"}


# ---------------------------------------------------------------------------
# Unit: emit validation
# ---------------------------------------------------------------------------

def test_emit_undeclared_event_raises_key_error():
    class MyProcess(RealTimeProcess):
        emits = ["tick"]
        def setup(self): pass

    p = MyProcess()
    with pytest.raises(KeyError, match="Undeclared event"):
        p.emit("not_declared")


# ---------------------------------------------------------------------------
# Unit: duplicate @on handler
# ---------------------------------------------------------------------------

def test_duplicate_on_handler_for_same_event_raises():
    class BadProcess(RealTimeProcess):
        listens = ["tick"]
        def setup(self): pass

        @on("tick")
        def handler_a(self): pass

        @on("tick")
        def handler_b(self): pass

    with pytest.raises(TypeError, match="Duplicate"):
        BadProcess()   # TypeError raised in __init__, not at class definition


# ---------------------------------------------------------------------------
# Unit: session connect() validation
# ---------------------------------------------------------------------------

def test_connect_event_missing_from_src_emits_raises(tmp_path):
    class Src(RealTimeProcess):
        emits = []
        def setup(self): pass

    class Dst(RealTimeProcess):
        listens = ["tick"]
        def setup(self): pass

    yaml = tmp_path / "project.yaml"
    yaml.write_text("diagram:\n  blocks: []\n")
    session = RealTimeSession(str(yaml))
    src, dst = Src(), Dst()
    session.add(src, dst)
    with pytest.raises(ValueError, match="not in"):
        session.connect("tick", src, dst)


def test_connect_event_missing_from_dst_listens_raises(tmp_path):
    class Src(RealTimeProcess):
        emits = ["tick"]
        def setup(self): pass

    class Dst(RealTimeProcess):
        listens = []
        def setup(self): pass

    yaml = tmp_path / "project.yaml"
    yaml.write_text("diagram:\n  blocks: []\n")
    session = RealTimeSession(str(yaml))
    src, dst = Src(), Dst()
    session.add(src, dst)
    with pytest.raises(ValueError, match="not in"):
        session.connect("tick", src, dst)


def test_connect_succeeds_when_event_in_gate_wait_for(tmp_path):
    """An event referenced in a Gate's wait_for counts as a valid listener."""
    class Src(RealTimeProcess):
        emits = ["sensor"]
        def setup(self): pass

    class Dst(RealTimeProcess):
        listens = []
        gates = [Gate("tick", wait_for=["sensor"])]
        def setup(self): pass

    yaml = tmp_path / "project.yaml"
    yaml.write_text("diagram:\n  blocks: []\n")
    session = RealTimeSession(str(yaml))
    src, dst = Src(), Dst()
    session.add(src, dst)
    session.connect("sensor", src, dst)   # must not raise


# ---------------------------------------------------------------------------
# Unit: _parse_io_specs
# ---------------------------------------------------------------------------

def test_parse_io_specs_extracts_external_blocks(tmp_path):
    yaml = tmp_path / "project.yaml"
    yaml.write_text("""
diagram:
  blocks:
    - name: Sensor
      type: external_input
      parameters:
        size: 3
    - name: Cmd
      type: external_output
      parameters:
        size: 2
    - name: Filter
      type: gain
""")
    specs = _parse_io_specs(str(yaml))
    assert specs == {"Sensor": 3, "Cmd": 2}


def test_parse_io_specs_defaults_size_to_one(tmp_path):
    yaml = tmp_path / "project.yaml"
    yaml.write_text("""
diagram:
  blocks:
    - name: U
      type: external_input
""")
    specs = _parse_io_specs(str(yaml))
    assert specs["U"] == 1


def test_parse_io_specs_empty_diagram(tmp_path):
    yaml = tmp_path / "project.yaml"
    yaml.write_text("diagram:\n  blocks: []\n")
    assert _parse_io_specs(str(yaml)) == {}


# ---------------------------------------------------------------------------
# Integration: single-event delivery
# ---------------------------------------------------------------------------

def test_single_event_reaches_consumer(tmp_path):
    """
    Producer emits one event after writing to shared memory.
    Consumer must handle it and copy the value into a multiprocessing.Array.
    """
    result = multiprocessing.Array("d", [0.0])

    class Producer(RealTimeProcess):
        emits = ["data_ready"]
        def setup(self): pass
        def run(self):
            self.setup()
            time.sleep(0.05)          # let consumer enter dispatch loop
            self.shared.Value = np.array([42.0])
            self.emit("data_ready")
            time.sleep(2.0)

    class Consumer(RealTimeProcess):
        listens = ["data_ready"]
        def setup(self): pass

        @on("data_ready")
        def handle(self):
            result[0] = float(self.shared.Value[0])

    prod, cons = Producer(), Consumer()
    # Keep session alive until after fork: if GC'd before p.start(), the
    # shutdown write-end closes and _dispatch_loop exits immediately via EOF.
    _sess = _session(tmp_path, prod, cons,
                     connections=[("data_ready", prod, cons)],
                     shared=[("Value", 1)])

    _start_and_stop([prod, cons])
    del _sess

    assert result[0] == pytest.approx(42.0)


# ---------------------------------------------------------------------------
# Integration: Gate fires only when all events have arrived
# ---------------------------------------------------------------------------

def test_gate_fires_after_all_required_events(tmp_path):
    """
    Controller's Gate waits for sensor_ready AND gui_command.
    It must fire exactly once after both producers have emitted.
    """
    fire_count = multiprocessing.Value("i", 0)
    result = multiprocessing.Array("d", [0.0, 0.0])

    class SensorProc(RealTimeProcess):
        emits = ["sensor_ready"]
        def setup(self): pass
        def run(self):
            self.setup()
            time.sleep(0.05)
            self.shared.Sensor = np.array([10.0])
            self.emit("sensor_ready")
            time.sleep(2.0)

    class GuiProc(RealTimeProcess):
        emits = ["gui_command"]
        def setup(self): pass
        def run(self):
            self.setup()
            time.sleep(0.10)
            self.shared.Gui = np.array([5.0])
            self.emit("gui_command")
            time.sleep(2.0)

    class Controller(RealTimeProcess):
        listens = []
        gates = [Gate("tick", wait_for=["sensor_ready", "gui_command"])]
        def setup(self): pass

        @on("tick")
        def control(self):
            fire_count.value += 1
            s = self.shared.read("Sensor", "Gui")
            result[0] = float(s["Sensor"][0])
            result[1] = float(s["Gui"][0])

    sensor, gui, ctrl = SensorProc(), GuiProc(), Controller()
    _sess = _session(tmp_path, sensor, gui, ctrl,
                     connections=[
                         ("sensor_ready", sensor, ctrl),
                         ("gui_command",  gui,    ctrl),
                     ],
                     shared=[("Sensor", 1), ("Gui", 1)])

    _start_and_stop([sensor, gui, ctrl])
    del _sess

    assert fire_count.value == 1
    assert result[0] == pytest.approx(10.0)
    assert result[1] == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Integration: both @on handlers fire independently (dispatch loop fix)
# ---------------------------------------------------------------------------

def test_both_handlers_fire_independently(tmp_path):
    """
    A Reactor with two independent @on handlers must fire BOTH, even when
    the events arrive at different times.  This is the core regression test
    for the sequential-wait bug fixed in _dispatch_loop.
    """
    count_a = multiprocessing.Value("i", 0)
    count_b = multiprocessing.Value("i", 0)

    class SrcA(RealTimeProcess):
        emits = ["ev_a"]
        def setup(self): pass
        def run(self):
            self.setup()
            time.sleep(0.05)
            self.emit("ev_a")
            time.sleep(2.0)

    class SrcB(RealTimeProcess):
        emits = ["ev_b"]
        def setup(self): pass
        def run(self):
            self.setup()
            time.sleep(0.15)         # arrives noticeably later than ev_a
            self.emit("ev_b")
            time.sleep(2.0)

    class Reactor(RealTimeProcess):
        listens = ["ev_a", "ev_b"]
        def setup(self): pass

        @on("ev_a")
        def on_a(self):
            count_a.value += 1

        @on("ev_b")
        def on_b(self):
            count_b.value += 1

    src_a, src_b, reactor = SrcA(), SrcB(), Reactor()
    _sess = _session(tmp_path, src_a, src_b, reactor,
                     connections=[
                         ("ev_a", src_a, reactor),
                         ("ev_b", src_b, reactor),
                     ])

    _start_and_stop([src_a, src_b, reactor])
    del _sess

    assert count_a.value == 1
    assert count_b.value == 1


# ---------------------------------------------------------------------------
# Integration: graceful shutdown
# ---------------------------------------------------------------------------

def test_shutdown_exits_dispatch_loop(tmp_path):
    """
    session._shutdown() must terminate all processes within its timeout.
    No process must remain alive after the call returns.
    """
    class IdleProcess(RealTimeProcess):
        listens = ["ev"]
        def setup(self): pass

        @on("ev")
        def handle(self): pass

    p = IdleProcess()
    session = _session(tmp_path, p)

    p.start()
    time.sleep(0.05)
    session._shutdown()

    assert not p.is_alive()
