import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.operators.gain import Gain


# ------------------------------------------------------------
# Helper : run a tiny simulation and return last output sample
# ------------------------------------------------------------
def run_sim(const_value, gain_block, dt=0.1):
    m = Model()

    src = Constant("src", const_value)
    m.add_block(src)
    m.add_block(gain_block)

    m.connect("src", "out", gain_block.name, "in")

    sim_cfg = SimulationConfig(dt, dt, logging=[f"{gain_block.name}.outputs.out"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs[f"{gain_block.name}.outputs.out"][-1]


# ------------------------------------------------------------
# 1) Element-wise mode (default)
# ------------------------------------------------------------
def test_gain_elementwise_scalar():
    out = run_sim([[2.0]], Gain("G", gain=3.0))
    assert np.allclose(out, [[6.0]])


def test_gain_elementwise_vector_row_scaling():
    # gain vector scales rows: y = [2,3]^T * u
    # u must have shape (2, ncols)
    out = run_sim([[1.0], [1.0]], Gain("G", gain=[2.0, 3.0]))
    assert np.allclose(out, [[2.0], [3.0]])


def test_gain_elementwise_vector_bad_u_rows():
    g = Gain("G", gain=[1.0, 2.0])  # len=2, expects u.shape[0]==2

    m = Model()
    src = Constant("src", [[1.0], [2.0], [3.0]])  # shape (3,1) incompatible
    m.add_block(src)
    m.add_block(g)
    m.connect("src", "out", "G", "in")

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)
    with pytest.raises(RuntimeError) as err:
        sim.initialize()

    # Simulator wraps the exception message during initialization
    assert "Element-wise mode requires u.shape[0] == len(gain)" in str(err.value)


def test_gain_elementwise_matrix_same_shape():
    K = np.array([[2.0, 0.0],
                  [1.0, -1.0]])
    u = np.array([[3.0, 4.0],
                  [1.0, 2.0]])
    out = run_sim(u, Gain("G", gain=K))
    assert np.allclose(out, K * u)


def test_gain_elementwise_matrix_bad_shape():
    K = np.zeros((2, 2))
    g = Gain("G", gain=K)

    m = Model()
    src = Constant("src", np.zeros((2, 3)))  # mismatch
    m.add_block(src)
    m.add_block(g)
    m.connect("src", "out", "G", "in")

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)
    with pytest.raises(RuntimeError) as err:
        sim.initialize()

    assert "Element-wise mode with matrix gain requires u.shape == gain.shape" in str(err.value)


# ------------------------------------------------------------
# 2) Matrix (K @ u)
# ------------------------------------------------------------
def test_gain_left_matrix_product():
    K = [[2.0, 0.0],
         [1.0, -1.0]]
    G = Gain("G", gain=K, multiplication="Matrix (K @ u)")

    out = run_sim([[3.0], [1.0]], G)
    # Expected: [[2*3 + 0*1], [1*3 + -1*1]] = [[6], [2]]
    assert np.allclose(out, [[6.0], [2.0]])


def test_gain_left_matrix_bad_dimensions():
    K = [[1.0, 2.0]]  # shape (1,2)
    g = Gain("G", gain=K, multiplication="Matrix (K @ u)")

    m = Model()
    src = Constant("src", [[1.0], [2.0], [3.0]])  # shape (3,1), incompatible
    m.add_block(src)
    m.add_block(g)
    m.connect("src", "out", "G", "in")

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)
    with pytest.raises(RuntimeError) as err:
        sim.initialize()

    assert "Left matrix product requires u.shape[0] == gain.shape[1]" in str(err.value)


def test_gain_left_matrix_requires_matrix_gain():
    g = Gain("G", gain=2.0, multiplication="Matrix (K @ u)")  # scalar gain not allowed here
    m = Model()
    src = Constant("src", [[1.0]])
    m.add_block(src)
    m.add_block(g)
    m.connect("src", "out", "G", "in")

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)
    with pytest.raises(RuntimeError) as err:
        sim.initialize()

    assert "requires a 2D matrix gain" in str(err.value)


# ------------------------------------------------------------
# 3) Matrix (u @ K)
# ------------------------------------------------------------
def test_gain_right_matrix_product():
    # u shape (1,2), K shape (2,3) => out shape (1,3)
    K = np.array([[1.0, 2.0, 3.0],
                  [4.0, 5.0, 6.0]])
    G = Gain("G", gain=K, multiplication="Matrix (u @ K)")

    out = run_sim(np.array([[10.0, 1.0]]), G)
    expected = np.array([[10.0, 1.0]]) @ K
    assert np.allclose(out, expected)


def test_gain_right_matrix_bad_dimensions():
    K = np.zeros((2, 3))
    g = Gain("G", gain=K, multiplication="Matrix (u @ K)")

    m = Model()
    src = Constant("src", np.zeros((1, 4)))  # u.shape[1]=4, expected 2
    m.add_block(src)
    m.add_block(g)
    m.connect("src", "out", "G", "in")

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)
    with pytest.raises(RuntimeError) as err:
        sim.initialize()

    assert "Right matrix product requires u.shape[1] == gain.shape[0]" in str(err.value)


# ------------------------------------------------------------
# 4) Initialization sanity
# ------------------------------------------------------------
def test_initialization_output_elementwise_default():
    G = Gain("G", gain=2.0)  # default: Element wise
    m = Model()
    src = Constant("src", [[1.5]])
    m.add_block(src)
    m.add_block(G)
    m.connect("src", "out", "G", "in")

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)
    sim.initialize(0.0)

    assert np.allclose(G.outputs["out"], [[3.0]])
