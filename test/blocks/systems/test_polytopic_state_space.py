import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.systems.polytopic_state_space import PolytopicStateSpace


def run_sim(src_w, src_u, sys, dt=0.1, T=0.3):
    m = Model()
    m.add_block(src_w)
    m.add_block(src_u)
    m.add_block(sys)
    m.connect(src_w.name, "out", sys.name, "w")
    m.connect(src_u.name, "out", sys.name, "u")

    sim_cfg = SimulationConfig(dt, T, logging=[f"{sys.name}.outputs.y", f"{sys.name}.outputs.x"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs


def test_poly_scalar_basic():
    # r=2, nx=1, nu=1, ny=1
    A = [[0.8, 0.5]]   # [A1 A2]
    B = [[1.0, 2.0]]   # [B1 B2]
    C = [[1.0]]

    src_w = Constant("w", [[0.25], [0.75]])
    src_u = Constant("u", [[2.0]])
    sys = PolytopicStateSpace("sys", A=A, B=B, C=C, x0=[[0.0]])

    logs = run_sim(src_w, src_u, sys)
    y = logs["sys.outputs.y"]
    x = logs["sys.outputs.x"]

    # x[k+1] = 0.575*x[k] + 3.5
    assert np.allclose(y[0], [[0.0]])
    assert np.allclose(x[1], [[3.5]])
    assert np.allclose(y[1], [[3.5]])
    assert np.allclose(x[2], [[5.5125]])
    assert np.allclose(y[2], [[5.5125]])


def test_poly_vector_dimensions():
    # r=2, nx=2, nu=1, ny=1
    A1 = np.array([[1.0, 0.1], [0.0, 1.0]])
    A2 = np.array([[0.9, 0.0], [0.0, 0.95]])
    A = np.hstack([A1, A2])

    B1 = np.array([[0.0], [1.0]])
    B2 = np.array([[1.0], [0.0]])
    B = np.hstack([B1, B2])
    C = np.array([[1.0, 0.0]])

    src_w = Constant("w", [[0.2], [0.8]])
    src_u = Constant("u", [[2.0]])
    sys = PolytopicStateSpace("sys", A=A, B=B, C=C, x0=[[0.0], [0.0]])

    logs = run_sim(src_w, src_u, sys)
    x = logs["sys.outputs.x"]
    y = logs["sys.outputs.y"]

    assert np.allclose(x[1], [[1.6], [0.4]])
    assert np.allclose(y[1], [[1.6]])
    assert np.allclose(x[2], [[3.08], [0.784]])
    assert np.allclose(y[2], [[3.08]])


def test_poly_missing_w_input_raises():
    A = [[1.0, 0.0]]
    B = [[1.0, 1.0]]
    C = [[1.0]]

    src_u = Constant("u", [[1.0]])
    sys = PolytopicStateSpace("sys", A=A, B=B, C=C)

    m = Model()
    m.add_block(src_u)
    m.add_block(sys)
    m.connect("u", "out", "sys", "u")

    sim_cfg = SimulationConfig(0.1, 0.1, logging=["sys.outputs.y"])
    sim = Simulator(m, sim_cfg)
    sim.initialize()

    with pytest.raises(RuntimeError):
        sim.run()


def test_poly_rejects_non_column_w():
    A = [[1.0, 0.0]]
    B = [[1.0, 1.0]]
    C = [[1.0]]

    src_w = Constant("w", [[0.2, 0.8], [0.1, 0.9]])  # 2x2, not column vector
    src_u = Constant("u", [[1.0]])
    sys = PolytopicStateSpace("sys", A=A, B=B, C=C)

    m = Model()
    m.add_block(src_w)
    m.add_block(src_u)
    m.add_block(sys)
    m.connect("w", "out", "sys", "w")
    m.connect("u", "out", "sys", "u")

    sim_cfg = SimulationConfig(0.1, 0.1, logging=["sys.outputs.y"])
    sim = Simulator(m, sim_cfg)

    with pytest.raises(ValueError) as err:
        sim.run()

    assert "must be a column vector" in str(err.value)


def test_poly_invalid_matrix_dimensions():
    C = [[1.0]]

    # A has nx=1 but 3 columns -> not (nx, r*nx)
    with pytest.raises(ValueError):
        PolytopicStateSpace("sys1", A=[[1.0, 2.0, 3.0]], B=[[1.0, 1.0]], C=C)

    # A => nx=1, r=2, so B must have 2*nu columns
    with pytest.raises(ValueError):
        PolytopicStateSpace("sys2", A=[[1.0, 2.0]], B=[[1.0, 2.0, 3.0]], C=C)

    # C has wrong number of columns
    with pytest.raises(ValueError):
        PolytopicStateSpace("sys3", A=[[1.0, 2.0]], B=[[1.0, 1.0]], C=[[1.0, 2.0]])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
