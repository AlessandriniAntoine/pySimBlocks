import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.step import Step
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.operators.discrete_derivator import DiscreteDerivator


# ------------------------------------------------------------
def run_sim(src_block, der_block, dt=0.1, T=0.3):
    m = Model()
    m.add_block(src_block)
    m.add_block(der_block)
    m.connect(src_block.name, "out", der_block.name, "in")

    sim_cfg = SimulationConfig(dt, T, logging=[f"{der_block.name}.outputs.out"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs[f"{der_block.name}.outputs.out"]


# ------------------------------------------------------------
def test_derivator_scalar_basic_step():
    """
    Step: value_before=0 until t=0.1, then 1.
    dt=0.1

    Expected derivative (backward difference):
      first output_update: 0 (placeholder)
      then at t=0.1: (1-0)/0.1 = 10
      then: 0
    """
    src = Step("src", start_time=0.1, value_before=[[0.0]], value_after=[[1.0]])
    D = DiscreteDerivator("D")

    logs = run_sim(src, D, dt=0.1, T=0.3)

    assert np.allclose(logs[0], [[0.0]])
    assert np.allclose(logs[1], [[10.0]])
    assert np.allclose(logs[2], [[0.0]])


# ------------------------------------------------------------
def test_derivator_vector_step():
    src = Step(
        "src",
        start_time=0.1,
        value_before=[[0.0], [0.0]],
        value_after=[[2.0], [4.0]],
    )
    D = DiscreteDerivator("D")

    logs = run_sim(src, D, dt=0.1, T=0.3)

    assert np.allclose(logs[0], [[0.0], [0.0]])
    assert np.allclose(logs[1], [[20.0], [40.0]])
    assert np.allclose(logs[2], [[0.0], [0.0]])


# ------------------------------------------------------------
def test_derivator_matrix_constant_is_zero():
    src = Constant("src", [[1.0, 2.0], [3.0, 4.0]])
    D = DiscreteDerivator("D")

    logs = run_sim(src, D, dt=0.1, T=0.3)

    # first call: 0 placeholder upgraded to matrix on first non-scalar input
    assert logs[0].shape == (2, 2)
    assert np.allclose(logs[0], np.zeros((2, 2)))

    # constant input -> derivative zero
    assert np.allclose(logs[1], np.zeros((2, 2)))
    assert np.allclose(logs[2], np.zeros((2, 2)))


# ------------------------------------------------------------
def test_derivator_initial_output_freezes_shape():
    """
    initial_output fixes the shape (including scalar).
    If input later has a different shape -> error.
    """
    D = DiscreteDerivator("D", initial_output=[[5.0]])  # freezes to (1,1)
    src = Constant("src", [[1.0, 2.0], [3.0, 4.0]])     # (2,2) -> mismatch

    m = Model()
    m.add_block(src)
    m.add_block(D)
    m.connect("src", "out", "D", "in")

    sim_cfg = SimulationConfig(0.1, 0.2, logging=["D.outputs.out"])
    sim = Simulator(m, sim_cfg)

    with pytest.raises(RuntimeError) as err:
        sim.run()

    assert "shape" in str(err.value).lower()


# ------------------------------------------------------------
def test_derivator_missing_input_never_none_output():
    """
    If the block is alone / never receives input, it must not propagate None.
    It will just keep (1,1) zeros (placeholder).
    """
    D = DiscreteDerivator("D")
    m = Model()
    m.add_block(D)

    sim_cfg = SimulationConfig(0.1, 0.2, logging=["D.outputs.out"])
    sim = Simulator(m, sim_cfg)

    logs = sim.run()
    assert np.allclose(logs["D.outputs.out"][0], [[0.0]])


# ------------------------------------------------------------
def test_derivator_shape_upgrade_from_placeholder_unit():
    """
    Unit test without simulator:
      - Start with no input -> placeholder output (1,1)
      - Then feed matrix -> shape freezes and u_prev set to avoid spike
    """
    D = DiscreteDerivator("D")
    D.initialize(0.0)

    # First output_update with missing input -> should keep placeholder, not crash
    D.inputs["in"] = None
    D.output_update(0.0, 0.1)
    assert np.allclose(D.outputs["out"], [[0.0]])

    # Now provide a matrix; first call after upgrade keeps 0 (but shape becomes (2,2))
    D.inputs["in"] = np.array([[1.0, 2.0], [3.0, 4.0]])
    D.output_update(0.1, 0.1)
    assert D.outputs["out"].shape == (2, 2)
    assert np.allclose(D.outputs["out"], np.zeros((2, 2)))

    # Second call with same matrix -> derivative zero
    D.state_update(0.1, 0.1)
    D.state["u_prev"] = D.next_state["u_prev"].copy()

    D.output_update(0.2, 0.1)
    assert np.allclose(D.outputs["out"], np.zeros((2, 2)))


# ------------------------------------------------------------
def test_derivator_shape_change_after_freeze_raises_unit():
    D = DiscreteDerivator("D")
    D.initialize(0.0)

    # First: provide matrix -> freezes
    D.inputs["in"] = np.array([[1.0, 2.0], [3.0, 4.0]])
    D.output_update(0.0, 0.1)

    # Now attempt incompatible shape
    D.inputs["in"] = np.array([[1.0], [2.0], [3.0]])
    with pytest.raises(ValueError) as err:
        D.output_update(0.1, 0.1)

    assert "shape" in str(err.value).lower()
