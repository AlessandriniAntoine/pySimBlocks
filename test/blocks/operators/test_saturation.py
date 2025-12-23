import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.sources.step import Step
from pySimBlocks.blocks.operators.saturation import Saturation


# ------------------------------------------------------------
# Helper
# ------------------------------------------------------------
def run_sim(src_block, sat_block, dt=0.1, T=0.2):
    m = Model()
    m.add_block(src_block)
    m.add_block(sat_block)
    m.connect(src_block.name, "out", sat_block.name, "in")

    sim_cfg = SimulationConfig(dt, T, logging=[f"{sat_block.name}.outputs.out"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs[f"{sat_block.name}.outputs.out"]


# ------------------------------------------------------------
# 1) Scalar saturation
# ------------------------------------------------------------
def test_saturation_scalar():
    src = Constant("src", 5.0)
    sat = Saturation("sat", u_min=0.0, u_max=3.0)

    logs = run_sim(src, sat)

    assert np.allclose(logs[0], [[3.0]])


# ------------------------------------------------------------
# 2) No saturation when bounds are wide
# ------------------------------------------------------------
def test_saturation_no_effect():
    src = Constant("src", 2.0)
    sat = Saturation("sat", u_min=-10.0, u_max=10.0)

    logs = run_sim(src, sat)

    assert np.allclose(logs[0], [[2.0]])


# ------------------------------------------------------------
# 3) Lower bound only
# ------------------------------------------------------------
def test_saturation_lower_only():
    src = Constant("src", -5.0)
    sat = Saturation("sat", u_min=-2.0)

    logs = run_sim(src, sat)

    assert np.allclose(logs[0], [[-2.0]])


# ------------------------------------------------------------
# 4) Upper bound only
# ------------------------------------------------------------
def test_saturation_upper_only():
    src = Constant("src", 5.0)
    sat = Saturation("sat", u_max=1.5)

    logs = run_sim(src, sat)

    assert np.allclose(logs[0], [[1.5]])


# ------------------------------------------------------------
# 5) Vector saturation
# ------------------------------------------------------------
def test_saturation_vector():
    src = Constant("src", [[5.0], [-5.0]])
    sat = Saturation("sat", u_min=[-1.0, -2.0], u_max=[3.0, -1.0])

    logs = run_sim(src, sat)

    assert np.allclose(logs[0], [[3.0], [-2.0]])


# ------------------------------------------------------------
# 6) Passthrough with no bounds
# ------------------------------------------------------------
def test_saturation_no_bounds():
    src = Step("src", value_before=0.0, value_after=10.0, start_time=0.0)
    sat = Saturation("sat")

    logs = run_sim(src, sat)

    assert np.allclose(logs[0], [[10.0]])


# ------------------------------------------------------------
# 7) Invalid bounds
# ------------------------------------------------------------
def test_saturation_invalid_bounds():
    with pytest.raises(ValueError):
        Saturation("sat", u_min=2.0, u_max=1.0)


# ------------------------------------------------------------
# 8) Missing input
# ------------------------------------------------------------
def test_saturation_missing_input():
    sat = Saturation("sat", u_min=0.0, u_max=1.0)
    m = Model()
    m.add_block(sat)

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)

    with pytest.raises(RuntimeError):
        sim.initialize()
