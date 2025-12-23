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
# 3) Automatic default signs = +1
# ------------------------------------------------------------
def test_sum_default_signs():
    sm = Sum("S")
    assert sm.signs == [1., 1.]


# ------------------------------------------------------------
# 4) Dimension mismatch must raise RuntimeError (wrapping ValueError)
# ------------------------------------------------------------
def test_sum_dimension_mismatch():
    m = Model()

    s1 = Constant("s1", [[1.0], [2.0]])  # 2x1
    s2 = Constant("s2", [[5.0]])         # 1x1 → mismatch

    sm = Sum("S", "++")
    m.add_block(s1)
    m.add_block(s2)
    m.add_block(sm)

    m.connect("s1", "out", "S", "in1")
    m.connect("s2", "out", "S", "in2")

    dt = 0.1
    sim_cfg = SimulationConfig(dt, dt, logging=["S.outputs.out"])
    sim = Simulator(m, sim_cfg)

    with pytest.raises(ValueError) as err:
        sim.run(T=0.1)

    assert "same dimension" in str(err.value)


# ------------------------------------------------------------
# 5) Invalid signs list
# ------------------------------------------------------------
def test_sum_invalid_signs():
    with pytest.raises(ValueError):
        Sum("S", signs="+/")  # 2 is invalid


# ------------------------------------------------------------
# 6) Inferred num_inputs from signs only
# ------------------------------------------------------------
def test_sum_infer_num_inputs_from_signs():
    sm = Sum("S", signs="+")
    assert sm.num_inputs == 1


# ------------------------------------------------------------
# 7) Check output initialization
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
