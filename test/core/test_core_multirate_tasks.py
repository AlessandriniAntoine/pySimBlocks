import numpy as np
import pytest

from pySimBlocks.core.block import Block
from pySimBlocks.core.model import Model
from pySimBlocks.core.config import SimulationConfig
from pySimBlocks.core.simulator import Simulator
from pySimBlocks.core.task import Task


class RateCounter(Block):
    """
    Stateful counter incremented on each activation (i.e., when the task runs).

    State:
        count[k+1] = count[k] + 1

    Output:
        y[k] = count[k]
    """

    def initialize(self, t0: float):
        self.state["count"] = np.array([[0.0]])
        self.outputs["y"] = np.array([[0.0]])

    def output_update(self, t: float, dt: float):
        self.outputs["y"] = np.array(self.state["count"])

    def state_update(self, t: float, dt: float):
        self.next_state["count"] = self.state["count"] + 1.0


def test_task_get_dt_semantics(capsys):
    """
    Contract test for Task.get_dt():
      - first activation returns Ts
      - subsequent calls return (t - last_activation)

    This test is isolated from Simulator (unit test of Task).
    """
    task = Task(Ts=0.1, blocks=[], global_output_order=[])

    assert task.get_dt(0.0) == pytest.approx(0.1)

    # Emulate one advance cycle (as Simulator would do)
    task.advance()  # last_activation becomes 0.0
    assert task.last_activation == pytest.approx(0.0)

    assert task.get_dt(0.3) == pytest.approx(0.3 - 0.0)


def test_multirate_activation_and_hold(capsys):
    """
    Validates that task activation controls execution:
      - fast block executes every dt (Ts = dt)
      - slow block executes every 2*dt (Ts = 2*dt)

    We log the slow state at every global tick; it must change only on its activations.
    """
    dt = 0.01
    T = 0.04  # logs at t = 0, 0.01, 0.02, 0.03, 0.04

    m = Model(name="multirate_test")
    m.add_block(RateCounter("fast", sample_time=dt))
    m.add_block(RateCounter("slow", sample_time=2 * dt))

    cfg = SimulationConfig(
        dt=dt,
        T=T,
        t0=0.0,
        solver="fixed",
        logging=["slow.state.count", "fast.state.count"],
    )
    sim = Simulator(model=m, sim_cfg=cfg, verbose=False)
    logs = sim.run()

    slow_count = np.array(logs["slow.state.count"]).flatten()
    fast_count = np.array(logs["fast.state.count"]).flatten()

    # # fast executes every tick -> after each step, count increases by 1
    assert np.allclose(fast_count, np.arange(1, len(fast_count) + 1))

    # # slow executes at t = 0, 0.02, 0.04 -> state after commit should be:
    # # t=0: 1, t=0.01: 1, t=0.02: 2, t=0.03: 2, t=0.04: 3
    expected = np.array([1, 1, 2, 2, 3], dtype=float)
    assert len(slow_count) == len(expected)
    assert np.allclose(slow_count, expected)
