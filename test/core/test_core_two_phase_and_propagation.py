import numpy as np
import pytest

from pySimBlocks.core.block import Block
from pySimBlocks.core.model import Model
from pySimBlocks.core.config import SimulationConfig
from pySimBlocks.core.simulator import Simulator


class SourceSetsOne(Block):
    """
    Test source that sets output to 0 at initialize and to 1 at each output_update.
    This is used to validate *immediate propagation* within Phase 1.
    """

    def initialize(self, t0: float):
        self.outputs["y"] = np.array([[0.0]])

    def output_update(self, t: float, dt: float):
        self.outputs["y"] = np.array([[1.0]])

    def state_update(self, t: float, dt: float):
        # Stateless
        self.next_state = self.state


class PassThrough(Block):
    """
    Test operator that forwards input u to output y.
    Raises if u is missing, to make propagation expectations explicit.
    """

    def initialize(self, t0: float):
        self.outputs["y"] = np.array([[0.0]])

    def output_update(self, t: float, dt: float):
        if "u" not in self.inputs:
            raise RuntimeError(f"[{self.name}] missing input 'u'")
        self.outputs["y"] = np.array(self.inputs["u"])

    def state_update(self, t: float, dt: float):
        self.next_state = self.state


class StatefulCounter(Block):
    """
    Test stateful block:
      - output y[k] = x[k]
      - next state x[k+1] = x[k] + 1

    Used to validate two-phase update semantics (outputs computed before state commit).
    """

    def initialize(self, t0: float):
        self.state["x"] = np.array([[0.0]])
        self.outputs["y"] = np.array([[0.0]])

    def output_update(self, t: float, dt: float):
        self.outputs["y"] = np.array(self.state["x"])

    def state_update(self, t: float, dt: float):
        self.next_state["x"] = self.state["x"] + 1.0


def _run(model: Model, dt: float, T: float, logging: list[str]):
    cfg = SimulationConfig(dt=dt, T=T, t0=0.0, solver="fixed", logging=logging)
    sim = Simulator(model=model, sim_cfg=cfg, verbose=False)
    sim.run()  # uses cfg.logging by default
    return sim.logs


def test_phase1_immediate_propagation(capsys):
    """
    Validates that outputs are propagated immediately after each output_update,
    not only at the end of Phase 1.

    Setup:
      src: outputs y=0 at initialize, y=1 at output_update
      dst: pass-through (y = u)
      connection: src.y -> dst.u

    Expectation:
      At the first tick (t=0), dst must see u=1 (the updated output), not u=0.
    """
    m = Model(name="propagation_test")
    m.add_block(SourceSetsOne("src"))
    m.add_block(PassThrough("dst"))
    m.connect("src", "y", "dst", "u")

    logs = _run(
        model=m,
        dt=0.01,
        T=0.01,
        logging=["dst.outputs.y", "src.outputs.y"],
    )

    # First logged sample corresponds to t_step = 0.0
    dst_y0 = float(logs["dst.outputs.y"][0][0, 0])
    src_y0 = float(logs["src.outputs.y"][0][0, 0])

    assert src_y0 == 1.0
    assert dst_y0 == 1.0


def test_two_phase_outputs_vs_state_commit(capsys):
    """
    Validates the strict two-phase semantics:
      - outputs at time t are computed from x[k]
      - state is committed to x[k+1] at end of step

    We log, per tick:
      - c.outputs.y  (expected: x[k])
      - c.state.x    (expected: x[k+1])

    Therefore, at each logged time:
      state_x == output_y + 1
    """
    m = Model(name="two_phase_test")
    m.add_block(StatefulCounter("c"))

    logs = _run(
        model=m,
        dt=0.01,
        T=0.04,  # gives samples at t = 0, 0.01, 0.02, 0.03, 0.04
        logging=["c.outputs.y", "c.state.x"],
    )

    y = np.array(logs["c.outputs.y"]).flatten()
    x = np.array(logs["c.state.x"]).flatten()

    assert len(y) == len(x) >= 3
    assert np.allclose(x, y + 1.0)
