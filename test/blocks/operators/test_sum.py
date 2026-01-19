import numpy as np
import pytest

from pySimBlocks.core.model import Model
from pySimBlocks.core.simulator import Simulator
from pySimBlocks.core.config import SimulationConfig
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.operators.sum import Sum


# ------------------------------------------------------------
# Helper
# ------------------------------------------------------------
def run_two_inputs(v1, v2, signs="++", dt=0.1):
    m = Model()

    s1 = Constant("s1", v1)
    s2 = Constant("s2", v2)

    m.add_block(s1)
    m.add_block(s2)

    sm = Sum("S", signs=signs)
    m.add_block(sm)

    m.connect("s1", "out", "S", "in1")
    m.connect("s2", "out", "S", "in2")

    sim_cfg = SimulationConfig(dt, dt, logging=["S.outputs.out"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs["S.outputs.out"][-1]


# ------------------------------------------------------------
# 1) Basic sum: u1 + u2
# ------------------------------------------------------------
def test_sum_basic():
    out = run_two_inputs([[1.0]], [[2.0]])
    assert np.allclose(out, [[3.0]])


# ------------------------------------------------------------
# 2) Subtraction: u1 - u2
# ------------------------------------------------------------
def test_sum_subtraction():
    out = run_two_inputs([[5.0]], [[3.0]], signs="+-")
    assert np.allclose(out, [[2.0]])


# ------------------------------------------------------------
# 3) Automatic default signs = ++
# ------------------------------------------------------------
def test_sum_default_signs():
    sm = Sum("S")
    assert sm.signs == [1.0, 1.0]
    assert sm.num_inputs == 2


# ------------------------------------------------------------
# 4) Matrix sum supported
# ------------------------------------------------------------
def test_sum_matrix_supported():
    u1 = np.array([[1.0, 2.0],
                   [3.0, 4.0]])
    u2 = np.array([[10.0, 20.0],
                   [30.0, 40.0]])
    out = run_two_inputs(u1, u2, signs="++")
    assert np.allclose(out, u1 + u2)


# ------------------------------------------------------------
# 5) Scalar broadcast to matrix supported (only (1,1) allowed)
# ------------------------------------------------------------
def test_sum_scalar_broadcast_to_matrix():
    u1 = np.array([[1.0, 2.0],
                   [3.0, 4.0]])
    u2 = np.array([[5.0]])  # scalar (1,1) broadcast
    out = run_two_inputs(u1, u2, signs="++")
    assert np.allclose(out, u1 + 5.0)


# ------------------------------------------------------------
# 6) Shape mismatch among non-scalars must raise RuntimeError
#    (sim wraps ValueError into RuntimeError)
# ------------------------------------------------------------
def test_sum_shape_mismatch_non_scalars():
    m = Model()

    s1 = Constant("s1", np.zeros((2, 2)))
    s2 = Constant("s2", np.zeros((2, 3)))  # mismatch

    sm = Sum("S", "++")
    m.add_block(s1)
    m.add_block(s2)
    m.add_block(sm)

    m.connect("s1", "out", "S", "in1")
    m.connect("s2", "out", "S", "in2")

    dt = 0.1
    sim_cfg = SimulationConfig(dt, dt, logging=["S.outputs.out"])
    sim = Simulator(m, sim_cfg)

    with pytest.raises(RuntimeError) as err:
        sim.run(T=0.1)

    assert "Inconsistent input shapes for Sum" in str(err.value)


# ------------------------------------------------------------
# 7) Vector-to-matrix implicit broadcast is NOT allowed
# ------------------------------------------------------------
def test_sum_vector_to_matrix_not_allowed():
    m = Model()

    s1 = Constant("s1", np.zeros((2, 2)))      # non-scalar target shape
    s2 = Constant("s2", np.zeros((2, 1)))      # non-scalar but different shape (not scalar)

    sm = Sum("S", "++")
    m.add_block(s1)
    m.add_block(s2)
    m.add_block(sm)

    m.connect("s1", "out", "S", "in1")
    m.connect("s2", "out", "S", "in2")

    dt = 0.1
    sim_cfg = SimulationConfig(dt, dt, logging=["S.outputs.out"])
    sim = Simulator(m, sim_cfg)

    with pytest.raises(RuntimeError) as err:
        sim.run(T=0.1)

    # depending on where it fails, message can be either "Inconsistent input shapes..."
    # or "Only scalar (1,1) inputs can be broadcast."
    assert (
        "Inconsistent input shapes for Sum" in str(err.value)
        or "Only scalar (1,1) inputs can be broadcast" in str(err.value)
    )


# ------------------------------------------------------------
# 8) Invalid signs list
# ------------------------------------------------------------
def test_sum_invalid_signs():
    with pytest.raises(ValueError):
        Sum("S", signs="+/")  # invalid character


# ------------------------------------------------------------
# 9) Inferred num_inputs from signs only
# ------------------------------------------------------------
def test_sum_infer_num_inputs_from_signs():
    sm = Sum("S", signs="+")
    assert sm.num_inputs == 1
    assert sm.signs == [1.0]


# ------------------------------------------------------------
# 10) Check output initialization (inputs connected)
# ------------------------------------------------------------
def test_sum_initial_output():
    m = Model()

    s1 = Constant("s1", [[1.0]])
    s2 = Constant("s2", [[2.0]])

    sm = Sum("S", signs="++")

    m.add_block(s1)
    m.add_block(s2)
    m.add_block(sm)

    m.connect("s1", "out", "S", "in1")
    m.connect("s2", "out", "S", "in2")

    dt = 0.1
    sim_cfg = SimulationConfig(dt, dt, logging=["S.outputs.out"])
    sim = Simulator(m, sim_cfg)
    sim.initialize(0.0)

    assert np.allclose(sm.outputs["out"], [[3.0]])
