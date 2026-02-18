import numpy as np
import pytest

from pySimBlocks.core.block import Block
from pySimBlocks.core.model import Model
from pySimBlocks.core.config import SimulationConfig
from pySimBlocks.core.simulator import Simulator


class RequiresInput(Block):
    """
    Block that explicitly requires an input port 'u'.
    Used to validate that missing inputs raise RuntimeError at evaluation time.
    """

    def initialize(self, t0: float):
        self.outputs["y"] = np.array([[0.0]])

    def output_update(self, t: float, dt: float):
        if "u" not in self.inputs:
            raise RuntimeError(f"[{self.name}] missing input 'u'")
        self.outputs["y"] = np.array(self.inputs["u"])

    def state_update(self, t: float, dt: float):
        self.next_state = self.state


class PureSource(Block):
    def __init__(self, name: str, value: float, sample_time: float | None = None):
        super().__init__(name=name, sample_time=sample_time)
        self.value = float(value)

    def initialize(self, t0: float):
        self.outputs["y"] = np.array([[self.value]])

    def output_update(self, t: float, dt: float):
        self.outputs["y"] = np.array([[self.value]])

    def state_update(self, t: float, dt: float):
        self.next_state = self.state


def _run(model: Model, cfg: SimulationConfig):
    sim = Simulator(model=model, sim_cfg=cfg, verbose=False)
    sim.run()
    return sim.logs


def test_missing_input_raises_runtime_error(capsys):
    m = Model(name="missing_input_test")
    m.add_block(RequiresInput("a"))

    cfg = SimulationConfig(dt=0.01, T=0.01, t0=0.0, solver="fixed", logging=["a.outputs.y"])

    with pytest.raises(RuntimeError):
        _run(m, cfg)


def test_determinism_same_model_same_logs(capsys):
    """
    Runs the same model twice and asserts identical logs.
    This freezes the determinism expectation of the core.
    """
    cfg = SimulationConfig(dt=0.01, T=0.03, t0=0.0, solver="fixed", logging=["p.outputs.y"])

    m1 = Model(name="determinism_test_1")
    m1.add_block(PureSource("s", value=2.0))
    m1.add_block(RequiresInput("p"))
    m1.connect("s", "y", "p", "u")

    logs1 = _run(m1, cfg)

    m2 = Model(name="determinism_test_2")
    m2.add_block(PureSource("s", value=2.0))
    m2.add_block(RequiresInput("p"))
    m2.connect("s", "y", "p", "u")

    logs2 = _run(m2, cfg)

    assert len(logs1["p.outputs.y"]) == len(logs2["p.outputs.y"])
    for v1, v2 in zip(logs1["p.outputs.y"], logs2["p.outputs.y"]):
        assert np.allclose(v1, v2)
