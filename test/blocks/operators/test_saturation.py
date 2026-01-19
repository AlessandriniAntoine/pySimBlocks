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
    src = Constant("src", 5.0)  # -> (1,1)
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
# 5) Vector bounds on vector input (m,1)
# ------------------------------------------------------------
def test_saturation_vector():
    src = Constant("src", [[5.0], [-5.0]])  # (2,1)
    sat = Saturation("sat", u_min=[-1.0, -2.0], u_max=[3.0, -1.0])  # -> (2,1)

    logs = run_sim(src, sat)
    assert np.allclose(logs[0], [[3.0], [-2.0]])


# ------------------------------------------------------------
# 6) Matrix input with scalar bounds
# ------------------------------------------------------------
def test_saturation_matrix_scalar_bounds():
    src = Constant("src", [[5.0, -5.0],
                           [2.0,  10.0]])  # (2,2)
    sat = Saturation("sat", u_min=0.0, u_max=3.0)  # scalar -> broadcast to (2,2)

    logs = run_sim(src, sat)
    expected = np.array([[3.0, 0.0],
                         [2.0, 3.0]])
    assert np.allclose(logs[0], expected)


# ------------------------------------------------------------
# 7) Matrix input with vector bounds (broadcast across columns)
# ------------------------------------------------------------
def test_saturation_matrix_vector_bounds_broadcast_columns():
    src = Constant("src", [[10.0, -10.0, 2.0],
                           [5.0,   6.0, -7.0]])  # (2,3)

    # bounds as (2,1) -> broadcast across columns
    sat = Saturation("sat", u_min=[0.0, -2.0], u_max=[3.0, 1.0])

    logs = run_sim(src, sat)

    # row1 clipped to [0,3], row2 clipped to [-2,1]
    expected = np.array([[3.0, 0.0, 2.0],
                         [1.0, 1.0, -2.0]])
    assert np.allclose(logs[0], expected)


# ------------------------------------------------------------
# 8) Passthrough with no bounds
# ------------------------------------------------------------
def test_saturation_no_bounds():
    src = Step("src", value_before=0.0, value_after=10.0, start_time=0.0)
    sat = Saturation("sat")

    logs = run_sim(src, sat)
    assert np.allclose(logs[0], [[10.0]])

# ------------------------------------------------------------
# 9) Invalid bounds (after resolution)
# ------------------------------------------------------------
def test_saturation_bounds_componentwise_ok():
    s = Saturation("sat", u_min=[1.0, 5.0], u_max=[2.0, 8.0])
    s.inputs["in"] = np.array([[0.0], [10.0]])
    s.initialize(0.0)
    assert np.allclose(s.outputs["out"], [[1.0], [8.0]])

# ------------------------------------------------------------
# 10) Invalid bounds (after resolution)
# ------------------------------------------------------------
def test_saturation_invalid_bounds_scalar():
    with pytest.raises(ValueError):
        s = Saturation("sat", u_min=2.0, u_max=1.0)
        s.inputs["in"] = np.array([[0.0]])
        s.initialize(0.0)


# ------------------------------------------------------------
# 11) Missing input at initialization
# ------------------------------------------------------------
def test_saturation_missing_input():
    sat = Saturation("sat", u_min=0.0, u_max=1.0)
    m = Model()
    m.add_block(sat)

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)

    with pytest.raises(RuntimeError):
        sim.initialize()


if __name__ == "__main__":
    test_saturation_invalid_bounds_scalar()
