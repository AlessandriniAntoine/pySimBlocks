import numpy as np
import pytest

from pySimBlocks.core.model import Model
from pySimBlocks.core.simulator import Simulator
from pySimBlocks.core.config import SimulationConfig
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.operators.product import Product


# ------------------------------------------------------------
# Helper
# ------------------------------------------------------------
def run_two_inputs(v1, v2, operations="*", dt=0.1):
    m = Model()

    s1 = Constant("s1", v1)
    s2 = Constant("s2", v2)

    m.add_block(s1)
    m.add_block(s2)

    pr = Product("P", operations=operations)
    m.add_block(pr)

    m.connect("s1", "out", "P", "in1")
    m.connect("s2", "out", "P", "in2")

    sim_cfg = SimulationConfig(dt, dt, logging=["P.outputs.out"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs["P.outputs.out"][-1]


# ------------------------------------------------------------
# 1) Basic product: u1 * u2
# ------------------------------------------------------------
def test_product_basic():
    out = run_two_inputs([[2.0]], [[3.0]])
    assert np.allclose(out, [[6.0]])


# ------------------------------------------------------------
# 2) Division: u1 / u2
# ------------------------------------------------------------
def test_product_division():
    out = run_two_inputs([[6.0]], [[3.0]], operations="/")
    assert np.allclose(out, [[2.0]])


# ------------------------------------------------------------
# 3) Scalar × vector (broadcast)
# ------------------------------------------------------------
def test_product_scalar_vector():
    out = run_two_inputs([[2.0]], [[1.0], [3.0], [4.0]])
    assert np.allclose(out, [[2.0], [6.0], [8.0]])


# ------------------------------------------------------------
# 4) Vector × vector (same dimension)
# ------------------------------------------------------------
def test_product_vector_vector():
    out = run_two_inputs([[2.0], [3.0]], [[4.0], [5.0]])
    assert np.allclose(out, [[8.0], [15.0]])


# ------------------------------------------------------------
# 5) Incompatible dimensions must raise ValueError
# ------------------------------------------------------------
def test_product_dimension_mismatch():
    m = Model()

    s1 = Constant("s1", [[1.0], [2.0]])  # 2x1
    s2 = Constant("s2", [[3.0], [4.0], [5.0]])  # 3x1

    pr = Product("P", operations="*")

    m.add_block(s1)
    m.add_block(s2)
    m.add_block(pr)

    m.connect("s1", "out", "P", "in1")
    m.connect("s2", "out", "P", "in2")

    dt = 0.1
    sim_cfg = SimulationConfig(dt, dt, logging=["P.outputs.out"])
    sim = Simulator(m, sim_cfg)

    with pytest.raises(RuntimeError) as err:
        sim.run(T=0.1)

    assert "Incompatible input dimensions" in str(err.value)


# ------------------------------------------------------------
# 6) Invalid operations string
# ------------------------------------------------------------
def test_product_invalid_operations():
    with pytest.raises(ValueError):
        Product("P", operations="*+")


# ------------------------------------------------------------
# 7) Inferred num_inputs from operations
# ------------------------------------------------------------
def test_product_infer_num_inputs_from_operations():
    pr = Product("P", operations="*/")
    assert pr.num_inputs == 3


# ------------------------------------------------------------
# 8) Check output initialization
# ------------------------------------------------------------
def test_product_initial_output():
    m = Model()

    s1 = Constant("s1", [[2.0]])
    s2 = Constant("s2", [[3.0]])

    pr = Product("P", operations="*")

    m.add_block(s1)
    m.add_block(s2)
    m.add_block(pr)

    m.connect("s1", "out", "P", "in1")
    m.connect("s2", "out", "P", "in2")

    dt = 0.1
    sim_cfg = SimulationConfig(dt, dt, logging=["P.outputs.out"])
    sim = Simulator(m, sim_cfg)
    sim.initialize(0.0)

    assert np.allclose(pr.outputs["out"], [[6.0]])

if __name__ == "__main__":
    test_product_dimension_mismatch()
