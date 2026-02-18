import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.controllers.state_feedback import StateFeedback


# ------------------------------------------------------------
# Helper: run a tiny simulation and return last u
# ------------------------------------------------------------
def run_sim(r_value, x_value, K, G, dt=0.1, T=0.1):
    m = Model()

    r_src = Constant("r_src", r_value)
    x_src = Constant("x_src", x_value)
    sf = StateFeedback("SF", K=K, G=G)

    m.add_block(r_src)
    m.add_block(x_src)
    m.add_block(sf)

    m.connect("r_src", "out", "SF", "r")
    m.connect("x_src", "out", "SF", "x")

    sim_cfg = SimulationConfig(dt, T, logging=["SF.outputs.u"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()

    return logs["SF.outputs.u"][-1]


# ------------------------------------------------------------
# 1) Nominal behavior
# ------------------------------------------------------------
def test_state_feedback_nominal():
    # K: (m,n) = (2,2), G: (m,p) = (2,1)
    K = np.array([[1.0, 2.0],
                  [0.5, -1.0]])
    G = np.array([[2.0],
                  [3.0]])

    r = np.array([[1.0]])          # (p,1)
    x = np.array([[4.0], [5.0]])   # (n,1)

    out = run_sim(r, x, K=K, G=G, dt=0.1, T=0.1)

    expected = G @ r - K @ x
    assert np.allclose(out, expected)
    assert out.shape == (2, 1)


# ------------------------------------------------------------
# 2) Constructor validation: K and G must be 2D
# ------------------------------------------------------------
def test_state_feedback_K_not_2d_raises():
    with pytest.raises(ValueError):
        StateFeedback("SF", K=[1.0, 2.0], G=[[1.0]])  # K is 1D


def test_state_feedback_G_not_2d_raises():
    with pytest.raises(ValueError):
        StateFeedback("SF", K=[[1.0, 2.0]], G=3.0)  # G is scalar


# ------------------------------------------------------------
# 3) Constructor validation: first dimension of K and G must match
# ------------------------------------------------------------
def test_state_feedback_KG_first_dim_mismatch_raises():
    K = np.zeros((2, 3))
    G = np.zeros((1, 1))  # m2 != m
    with pytest.raises(ValueError):
        StateFeedback("SF", K=K, G=G)


# ------------------------------------------------------------
# 4) Missing input in simulation: r connected but x missing -> RuntimeError
# ------------------------------------------------------------
def test_state_feedback_missing_input_x_raises_runtimeerror():
    K = np.array([[1.0, 0.0]])
    G = np.array([[1.0]])

    m = Model()
    r_src = Constant("r_src", [[1.0]])
    sf = StateFeedback("SF", K=K, G=G)

    m.add_block(r_src)
    m.add_block(sf)

    m.connect("r_src", "out", "SF", "r")
    # x not connected

    sim_cfg = SimulationConfig(0.1, 0.1, logging=["SF.outputs.u"])
    sim = Simulator(m, sim_cfg)

    with pytest.raises(RuntimeError) as err:
        sim.run()

    assert "input 'x'" in str(err.value).lower()


# ------------------------------------------------------------
# 5) Invalid input shape in simulation: x is matrix (n,2) -> RuntimeError
# ------------------------------------------------------------
def test_state_feedback_invalid_input_shape_raises_runtimeerror():
    K = np.array([[1.0, 0.0],
                  [0.0, 1.0]])  # (2,2)
    G = np.array([[1.0],
                  [1.0]])       # (2,1)

    r = np.array([[1.0]])             # ok (1,1)
    x_bad = np.array([[1.0, 2.0],     # bad (2,2)
                      [3.0, 4.0]])

    m = Model()
    r_src = Constant("r_src", r)
    x_src = Constant("x_src", x_bad)
    sf = StateFeedback("SF", K=K, G=G)

    m.add_block(r_src)
    m.add_block(x_src)
    m.add_block(sf)

    m.connect("r_src", "out", "SF", "r")
    m.connect("x_src", "out", "SF", "x")

    sim_cfg = SimulationConfig(0.1, 0.1, logging=["SF.outputs.u"])
    sim = Simulator(m, sim_cfg)

    with pytest.raises(ValueError) as err:
        sim.run()

    assert "must be a column vector" in str(err.value).lower()


# ------------------------------------------------------------
# 6) Wrong vector dimension: r has wrong rows -> RuntimeError
# ------------------------------------------------------------
def test_state_feedback_wrong_r_dimension_raises_valueerror():
    K = np.zeros((2, 2))
    G = np.zeros((2, 1))  # expects r shape (1,1)

    r_bad = np.array([[1.0], [2.0]])  # (2,1) -> wrong
    x = np.array([[0.0], [0.0]])

    m = Model()
    r_src = Constant("r_src", r_bad)
    x_src = Constant("x_src", x)
    sf = StateFeedback("SF", K=K, G=G)

    m.add_block(r_src)
    m.add_block(x_src)
    m.add_block(sf)

    m.connect("r_src", "out", "SF", "r")
    m.connect("x_src", "out", "SF", "x")

    sim_cfg = SimulationConfig(0.1, 0.1, logging=["SF.outputs.u"])
    sim = Simulator(m, sim_cfg)

    with pytest.raises(ValueError) as err:
        sim.run()

    assert "wrong dimension" in str(err.value).lower()
    assert "expected (1,1)" in str(err.value).lower()


# ------------------------------------------------------------
# 7) Shape freeze: once seen, input shape cannot change (direct block test)
# ------------------------------------------------------------
def test_state_feedback_shape_change_over_time_raises_valueerror_direct():
    K = np.array([[1.0, 0.0],
                  [0.0, 1.0]])  # (2,2)
    G = np.array([[1.0],
                  [1.0]])       # (2,1) -> expects r (1,1)

    sf = StateFeedback("SF", K=K, G=G)

    # First valid shapes
    sf.inputs["r"] = np.array([[1.0]])          # (1,1)
    sf.inputs["x"] = np.array([[2.0], [3.0]])   # (2,1)

    sf.initialize(0.0)
    sf.output_update(0.0, 0.1)

    # Now change x shape -> should raise (no implicit flatten, shape frozen)
    sf.inputs["x"] = np.array([[1.0], [2.0], [3.0]])  # (3,1)

    with pytest.raises(ValueError) as err:
        sf.output_update(0.1, 0.1)

    assert "has wrong dimension" in str(err.value).lower()

