import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.operators.gain import Gain


# ------------------------------------------------------------
# Helper : run a tiny simulation and return output
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
# 1) Scalar gain tests
# ------------------------------------------------------------
def test_gain_scalar():
    out = run_sim([[2.0]], Gain("G", gain=3.0))
    assert np.allclose(out, [[6.0]])


# ------------------------------------------------------------
# 2) Vector gain tests (m,)
# ------------------------------------------------------------
def test_gain_vector():
    # K = [2, 3], u = [[1]]
    out = run_sim([[1.0]], Gain("G", gain=[2.0, 3.0]))
    assert np.allclose(out, [[2.0], [3.0]])


def test_gain_vector_bad_u_shape():
    g = Gain("G", gain=[1.0, 2.0])
    m = Model()
    src = Constant("src", [[1.0], [2.0]])  # shape (2,1) incompatible
    m.add_block(src)
    m.add_block(g)
    m.connect("src", "out", "G", "in")

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)
    with pytest.raises(RuntimeError) as err:
        sim.initialize()
    assert "must be shape (1,1)" in str(err.value)




# ------------------------------------------------------------
# 3) Matrix gain tests (m,n)
# ------------------------------------------------------------
def test_gain_matrix():
    K = [[2.0, 0.0],
         [1.0, -1.0]]
    out = run_sim([[3.0], [1.0]], Gain("G", gain=K))
    # Expected: [[2*3 + 0*1], [1*3 + -1*1]] = [[6], [2]]
    assert np.allclose(out, [[6.0], [2.0]])


def test_gain_matrix_bad_dimensions():
    K = [[1.0, 2.0]]
    g = Gain("G", gain=K)

    m = Model()
    src = Constant("src", [[1.0], [2.0], [3.0]])  # shape (3,1), incompatible with K = (1,2)
    m.add_block(src)
    m.add_block(g)
    m.connect("src", "out", "G", "in")

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)
    with pytest.raises(RuntimeError) as err:
        sim.initialize()
    assert "Incompatible dimensions" in str(err.value)


# ------------------------------------------------------------
# 4) Initialization tests
# ------------------------------------------------------------
def test_initialization_output():
    G = Gain("G", gain=2.0)
    m = Model()
    src = Constant("src", [[1.5]])
    m.add_block(src)
    m.add_block(G)
    m.connect("src", "out", "G", "in")

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)
    sim.initialize(0.0)

    assert np.allclose(G.outputs["out"], [[3.0]])
