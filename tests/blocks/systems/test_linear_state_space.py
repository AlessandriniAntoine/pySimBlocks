import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.systems.linear_state_space import LinearStateSpace


# ------------------------------------------------------------
def run_sim(src, sys, dt=0.1, T=0.3):
    m = Model()
    m.add_block(src)
    m.add_block(sys)
    m.connect(src.name, "out", sys.name, "u")

    sim_cfg = SimulationConfig(dt, T, logging=[f"{sys.name}.outputs.y", f"{sys.name}.outputs.x"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs


# ------------------------------------------------------------
def test_lss_scalar_1state_basic():
    # x[k+1] = 0.9 x[k] + 1*u[k], y = x
    A = [[0.9]]
    B = [[1.0]]
    C = [[1.0]]

    src = Constant("u", [[1.0]])
    sys = LinearStateSpace("sys", A=A, B=B, C=C, x0=[[0.0]])

    logs = run_sim(src, sys, dt=0.1, T=0.3)

    y = logs["sys.outputs.y"]
    x = logs["sys.outputs.x"]

    # At t=0: x0=0 -> y0=0
    assert np.allclose(y[0], [[0.0]])
    assert np.allclose(x[0], [[0.0]])

    # Then x1 = 0 + 0.1*?  (No: discrete system is already discrete; dt not used in state update)
    # Here: x[k+1]=0.9 x[k] + 1*u[k]
    # Step-by-step with u=1:
    # x1 = 0.9*0 + 1 = 1
    # x2 = 0.9*1 + 1 = 1.9
    # y[k] = x[k]
    assert np.allclose(y[1], [[1.0]])
    assert np.allclose(y[2], [[1.9]])


# ------------------------------------------------------------
def test_lss_vector_dims():
    # n=2, m=1, p=1
    A = [[1.0, 0.1],
         [0.0, 1.0]]
    B = [[0.0],
         [1.0]]
    C = [[1.0, 0.0]]

    src = Constant("u", [[2.0]])
    sys = LinearStateSpace("sys", A=A, B=B, C=C, x0=[[0.0], [0.0]])

    logs = run_sim(src, sys, dt=0.1, T=0.3)

    y = logs["sys.outputs.y"]
    x = logs["sys.outputs.x"]

    # k=0: x0=[0,0], y0=0
    assert np.allclose(y[0], [[0.0]])

    # k=1: x1 = A x0 + B u = [0, 2]
    assert np.allclose(x[1], [[0.0], [2.0]])
    assert np.allclose(y[1], [[0.0]])

    # k=2: x2 = A x1 + B u = [0 + 0.1*2, 2] + [0,2] = [0.2, 4]
    assert np.allclose(x[2], [[0.2], [4.0]])
    assert np.allclose(y[2], [[0.2]])


# ------------------------------------------------------------
def test_lss_missing_input_raises():
    A = [[1.0]]
    B = [[1.0]]
    C = [[1.0]]
    sys = LinearStateSpace("sys", A=A, B=B, C=C)

    m = Model()
    m.add_block(sys)

    sim_cfg = SimulationConfig(0.1, 0.1, logging=["sys.outputs.y"])
    sim = Simulator(m, sim_cfg)
    sim.initialize()

    with pytest.raises(RuntimeError):
        sim.run()


# ------------------------------------------------------------
def test_lss_rejects_non_vector_u():
    A = [[1.0]]
    B = [[1.0]]
    C = [[1.0]]
    sys = LinearStateSpace("sys", A=A, B=B, C=C)

    # Provide u as 1x2 matrix via Constant -> invalid for u (must be (m,1)=(1,1))
    src = Constant("u", [[1.0, 2.0]])

    m = Model()
    m.add_block(src)
    m.add_block(sys)
    m.connect("u", "out", "sys", "u")

    sim_cfg = SimulationConfig(0.1, 0.1, logging=["sys.outputs.y"])
    sim = Simulator(m, sim_cfg)

    with pytest.raises(ValueError) as err:
        sim.run()

    assert "must be a column vector" in str(err.value) or "must have shape" in str(err.value)


# ------------------------------------------------------------
def test_lss_invalid_matrix_dimensions():
    # A is 2x2, B has wrong rows
    A = np.eye(2)
    B = np.ones((3, 1))  # wrong
    C = np.ones((1, 2))

    with pytest.raises(ValueError):
        LinearStateSpace("sys", A=A, B=B, C=C)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

