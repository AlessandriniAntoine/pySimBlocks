import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.step import Step
from pySimBlocks.blocks.operators.discrete_derivator import DiscreteDerivator


# ------------------------------------------------------------
def run_sim(src_block, der_block, dt=0.1, T=0.4):
    m = Model()
    m.add_block(src_block)
    m.add_block(der_block)
    m.connect(src_block.name, "out", der_block.name, "in")

    sim_cfg = SimulationConfig(dt, T, logging=[f"{der_block.name}.outputs.out"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs[f"{der_block.name}.outputs.out"]


# ------------------------------------------------------------
def test_derivator_scalar_basic():
    """
    Step at t=0.1: u = 0 (t=0.0), 1 (t=0.1), 1 (t=0.2), 1 (t=0.3)
    Backward diff: y = (u[k]-u[k-1])/dt -> 0, (1-0)/0.1=10, 0, 0
    """
    src = Step("src", start_time=0.1, value_before=0.0, value_after=1.0)
    D = DiscreteDerivator("D")

    logs = run_sim(src, D, dt=0.1, T=0.4)

    assert np.allclose(logs[0], [[0.0]])
    assert np.allclose(logs[1], [[10.0]])
    assert np.allclose(logs[2], [[0.0]])
    assert np.allclose(logs[3], [[0.0]])


# ------------------------------------------------------------
def test_derivator_vector():
    src = Step(
        "src",
        start_time=0.1,
        value_before=[[0.0], [0.0]],
        value_after=[[2.0], [4.0]],
    )
    D = DiscreteDerivator("D")

    logs = run_sim(src, D, dt=0.1, T=0.3)

    # t=0.0 -> 0
    # t=0.1 -> ( [2,4] - [0,0] ) / 0.1 = [20,40]
    # t=0.2 -> 0
    assert np.allclose(logs[0], [[0.0], [0.0]])
    assert np.allclose(logs[1], [[20.0], [40.0]])
    assert np.allclose(logs[2], [[0.0], [0.0]])


# ------------------------------------------------------------
def test_derivator_matrix():
    src = Step(
        "src",
        start_time=0.1,
        value_before=[[0.0, 0.0],
                      [0.0, 0.0]],
        value_after=[[1.0, 2.0],
                     [3.0, 4.0]],
    )
    D = DiscreteDerivator("D")

    logs = run_sim(src, D, dt=0.1, T=0.3)

    expected1 = np.array([[10.0, 20.0],
                          [30.0, 40.0]])  # (value_after - 0)/0.1

    assert np.allclose(logs[0], np.zeros((2, 2)))
    assert np.allclose(logs[1], expected1)
    assert np.allclose(logs[2], np.zeros((2, 2)))


# ------------------------------------------------------------
def test_derivator_initial_output():
    D = DiscreteDerivator("D", initial_output=[[5.0]])
    src = Step("src", start_time=0.0, value_before=[[0.0]], value_after=[[1.0]])

    logs = run_sim(src, D, dt=0.1, T=0.1)
    # first execution keeps initial_output
    assert np.allclose(logs[0], [[5.0]])


# ------------------------------------------------------------
def test_derivator_missing_input():
    D = DiscreteDerivator("D")
    m = Model()
    m.add_block(D)

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)
    sim.initialize()

    with pytest.raises(RuntimeError):
        sim.run()


# ------------------------------------------------------------
def test_derivator_input_shape_change_raises():
    # block-only test: once (1,1) is seen, shape cannot change
    D = DiscreteDerivator("D")
    D.inputs["in"] = np.array([[0.0]])
    D.initialize(0.0)
    D.output_update(0.0, 0.1)
    D.state_update(0.0, 0.1)

    D.inputs["in"] = np.array([[1.0, 2.0],
                               [3.0, 4.0]])
    with pytest.raises(ValueError) as err:
        D.output_update(0.1, 0.1)
    assert "shape" in str(err.value)
