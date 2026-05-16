import pytest
import numpy as np

from pySimBlocks.core.block import Block
from pySimBlocks.core.config import SimulationConfig
from pySimBlocks.core.model import Model
from pySimBlocks.core.simulator import Simulator
from pySimBlocks.real_time.real_time_runner import RealTimeRunner


# ---------------------------------------------------------------------------
# Minimal blocks
# ---------------------------------------------------------------------------

class EchoBlock(Block):
    """Passes inputs["in"] straight through to outputs["out"]."""
    direct_feedthrough = True

    def initialize(self, t0):
        self.outputs["out"] = np.zeros((1, 1))

    def output_update(self, t, dt):
        val = self.inputs.get("in")
        if val is not None:
            self.outputs["out"] = np.asarray(val, dtype=float)

    def state_update(self, t, dt):
        self.next_state = self.state


class AccumulatorBlock(Block):
    """State x[k+1] = x[k] + inputs["in"]; outputs x[k]."""
    direct_feedthrough = False

    def initialize(self, t0):
        self.state["x"] = np.zeros((1, 1))
        self.outputs["out"] = np.zeros((1, 1))

    def output_update(self, t, dt):
        self.outputs["out"] = self.state["x"].copy()

    def state_update(self, t, dt):
        val = self.inputs.get("in", np.zeros((1, 1)))
        self.next_state["x"] = self.state["x"] + np.asarray(val, dtype=float)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_runner(target_dt=None, time_source="perf_counter"):
    model = Model("rt_test")
    model.add_block(EchoBlock("io"))
    cfg = SimulationConfig(dt=0.01, T=100.0, clock="external", solver="fixed")
    sim = Simulator(model=model, sim_cfg=cfg)
    runner = RealTimeRunner(
        sim,
        input_blocks=["io"],
        output_blocks=["io"],
        target_dt=target_dt,
        time_source=time_source,
    )
    runner.initialize()
    return runner


# ---------------------------------------------------------------------------
# Basic tick behaviour
# ---------------------------------------------------------------------------

def test_tick_returns_output_for_known_block():
    runner = _make_runner()
    out = runner.tick({"io": np.array([[3.14]])}, dt=0.01)
    assert "io" in out
    assert float(out["io"][0, 0]) == pytest.approx(3.14)


def test_tick_output_is_column_vector():
    runner = _make_runner()
    out = runner.tick({"io": np.array([[1.0]])}, dt=0.01)
    assert out["io"].ndim == 2
    assert out["io"].shape[1] == 1


def test_tick_accumulates_over_multiple_steps():
    """
    AccumulatorBlock: output at step k is state x[k], which equals the sum of
    all inputs up to step k-1.  After 3 ticks with input=1, output must be 2.
    """
    model = Model("acc")
    model.add_block(AccumulatorBlock("acc"))
    cfg = SimulationConfig(dt=0.01, T=100.0, clock="external", solver="fixed")
    sim = Simulator(model=model, sim_cfg=cfg)
    runner = RealTimeRunner(sim, input_blocks=["acc"], output_blocks=["acc"])
    runner.initialize()

    out = {}
    for _ in range(3):
        out = runner.tick({"acc": np.array([[1.0]])}, dt=0.01)

    assert float(out["acc"][0, 0]) == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# dt handling
# ---------------------------------------------------------------------------

def test_tick_accepts_explicit_dt():
    runner = _make_runner()
    out = runner.tick({"io": np.array([[7.0]])}, dt=0.005)
    assert float(out["io"][0, 0]) == pytest.approx(7.0)


def test_tick_measures_wall_dt_when_no_dt_given():
    """
    When dt is omitted, the runner computes dt from the clock.
    We inject a fake clock so the measured dt is deterministic.
    """
    runner = _make_runner()
    runner._t_prev = 90.0
    runner._now = lambda: 90.05   # constant → dt_meas = 0.05 every call

    out = runner.tick({"io": np.array([[1.0]])})
    assert out is not None
    assert runner._t_prev == pytest.approx(90.05)


# ---------------------------------------------------------------------------
# Overrun warning
# ---------------------------------------------------------------------------

def test_tick_warns_when_dt_exceeds_budget(capsys):
    runner = _make_runner(target_dt=0.01)
    runner.tick({"io": np.array([[1.0]])}, dt=0.02)   # 0.02 > 1.5 × 0.01
    assert "Warning" in capsys.readouterr().out


def test_tick_no_warning_within_budget(capsys):
    runner = _make_runner(target_dt=0.1)
    runner.tick({"io": np.array([[1.0]])}, dt=0.01)
    assert "Warning" not in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Pacing
# ---------------------------------------------------------------------------

def test_tick_pace_sleeps_when_budget_remains(monkeypatch):
    """
    When pace=True and the step finishes before target_dt, the runner must
    sleep for the remaining budget.
    """
    slept = []
    monkeypatch.setattr(
        "pySimBlocks.real_time.real_time_runner.time.sleep",
        lambda s: slept.append(s),
    )
    runner = _make_runner(target_dt=1.0)
    # Fake clock: t_now=100.0, elapsed after step=0.001 → budget left ≈ 0.999
    runner._t_prev = 99.999
    times = iter([100.0, 100.001])
    runner._now = lambda: next(times)

    runner.tick({"io": np.array([[1.0]])}, dt=0.001, pace=True)

    assert len(slept) == 1
    assert slept[0] == pytest.approx(1.0 - 0.001, abs=0.01)


def test_tick_pace_does_not_sleep_when_over_budget(monkeypatch):
    """
    When the step itself already exceeded target_dt, sleep_time is negative
    and no sleep call must be made.
    """
    slept = []
    monkeypatch.setattr(
        "pySimBlocks.real_time.real_time_runner.time.sleep",
        lambda s: slept.append(s),
    )
    runner = _make_runner(target_dt=0.001)
    runner._t_prev = 100.0
    times = iter([100.0, 100.1])   # elapsed = 0.1 >> target_dt = 0.001
    runner._now = lambda: next(times)

    runner.tick({"io": np.array([[1.0]])}, dt=0.1, pace=True)

    assert len(slept) == 0


def test_tick_pace_false_never_sleeps(monkeypatch):
    slept = []
    monkeypatch.setattr(
        "pySimBlocks.real_time.real_time_runner.time.sleep",
        lambda s: slept.append(s),
    )
    runner = _make_runner(target_dt=1.0)
    runner.tick({"io": np.array([[1.0]])}, dt=0.001, pace=False)
    assert len(slept) == 0


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_tick_missing_input_raises_key_error():
    runner = _make_runner()
    with pytest.raises(KeyError, match="Missing input"):
        runner.tick({}, dt=0.01)


def test_runner_invalid_time_source_raises():
    model = Model("ts_test")
    model.add_block(EchoBlock("io"))
    cfg = SimulationConfig(dt=0.01, T=100.0, clock="external", solver="fixed")
    sim = Simulator(model=model, sim_cfg=cfg)
    with pytest.raises(ValueError, match="time_source"):
        RealTimeRunner(sim, input_blocks=["io"], output_blocks=["io"],
                       time_source="rdtsc")
