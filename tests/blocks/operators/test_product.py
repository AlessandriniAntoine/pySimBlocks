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
def run_two_inputs(v1, v2, operations="*", multiplication="Element-wise (*)", dt=0.1):
    m = Model()

    s1 = Constant("s1", v1)
    s2 = Constant("s2", v2)

    m.add_block(s1)
    m.add_block(s2)

    pr = Product("P", operations=operations, multiplication=multiplication)
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
# 3) Scalar × vector (broadcast scalar (1,1) only)
# ------------------------------------------------------------
def test_product_scalar_vector():
    out = run_two_inputs([[2.0]], [[1.0], [3.0], [4.0]])
    assert np.allclose(out, [[2.0], [6.0], [8.0]])


# ------------------------------------------------------------
# 4) Vector × vector (same shape)
# ------------------------------------------------------------
def test_product_vector_vector():
    out = run_two_inputs([[2.0], [3.0]], [[4.0], [5.0]])
    assert np.allclose(out, [[8.0], [15.0]])


# ------------------------------------------------------------
# 5) Matrix element-wise product (same shape)
# ------------------------------------------------------------
def test_product_matrix_elementwise():
    A = [[1.0, 2.0], [3.0, 4.0]]
    B = [[2.0, 0.5], [1.0, 2.0]]
    out = run_two_inputs(A, B, multiplication="Element-wise (*)")
    assert np.allclose(out, np.array(A) * np.array(B))


# ------------------------------------------------------------
# 6) Scalar × matrix (element-wise scalar broadcast)
# ------------------------------------------------------------
def test_product_scalar_matrix_elementwise():
    out = run_two_inputs([[2.0]], [[1.0, 2.0], [3.0, 4.0]], multiplication="Element-wise (*)")
    assert np.allclose(out, 2.0 * np.array([[1.0, 2.0], [3.0, 4.0]]))


# ------------------------------------------------------------
# 7) Incompatible shapes in element-wise must raise
# ------------------------------------------------------------
def test_product_shape_mismatch_elementwise():
    m = Model()

    s1 = Constant("s1", [[1.0], [2.0]])           # (2,1)
    s2 = Constant("s2", [[3.0, 4.0, 5.0]])        # (1,3) -> mismatch
    pr = Product("P", operations="*", multiplication="Element-wise (*)")

    m.add_block(s1)
    m.add_block(s2)
    m.add_block(pr)

    m.connect("s1", "out", "P", "in1")
    m.connect("s2", "out", "P", "in2")

    sim_cfg = SimulationConfig(0.1, 0.1, logging=["P.outputs.out"])
    sim = Simulator(m, sim_cfg)

    with pytest.raises(RuntimeError) as err:
        sim.run(T=0.1)

    assert "incompatible input shapes" in str(err.value).lower()


# ------------------------------------------------------------
# 8) Matrix multiplication (@) basic
# ------------------------------------------------------------
def test_product_matrix_multiplication():
    A = [[1.0, 2.0],
         [3.0, 4.0]]          # (2,2)
    B = [[5.0],
         [6.0]]               # (2,1)

    out = run_two_inputs(A, B, operations="*", multiplication="Matrix (@)")
    assert np.allclose(out, np.array(A) @ np.array(B))
    assert out.shape == (2, 1)


# ------------------------------------------------------------
# 9) Matrix multiplication rejects division
# ------------------------------------------------------------
def test_product_matrix_mode_rejects_division():
    with pytest.raises(ValueError):
        Product("P", operations="/", multiplication="Matrix (@)")


# ------------------------------------------------------------
# 10) Invalid operations string
# ------------------------------------------------------------
def test_product_invalid_operations():
    with pytest.raises(ValueError):
        Product("P", operations="*+")


# ------------------------------------------------------------
# 11) Inferred num_inputs from operations
# ------------------------------------------------------------
def test_product_infer_num_inputs_from_operations():
    pr = Product("P", operations="*/")
    assert pr.num_inputs == 3


# ------------------------------------------------------------
# 12) Check output initialization
# ------------------------------------------------------------
def test_product_initial_output():
    m = Model()

    s1 = Constant("s1", [[2.0]])
    s2 = Constant("s2", [[3.0]])

    pr = Product("P", operations="*", multiplication="Element-wise (*)")

    m.add_block(s1)
    m.add_block(s2)
    m.add_block(pr)

    m.connect("s1", "out", "P", "in1")
    m.connect("s2", "out", "P", "in2")

    sim_cfg = SimulationConfig(0.1, 0.1, logging=["P.outputs.out"])
    sim = Simulator(m, sim_cfg)
    sim.initialize(0.0)

    assert np.allclose(pr.outputs["out"], [[6.0]])
