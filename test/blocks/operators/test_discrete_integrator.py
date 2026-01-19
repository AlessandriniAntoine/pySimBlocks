import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.step import Step
from pySimBlocks.blocks.operators.discrete_integrator import DiscreteIntegrator


# ----------------------------------------------------------------------
def run_sim(src_block, integrator_block, dt=0.1, T=0.3):
    m = Model()
    m.add_block(src_block)
    m.add_block(integrator_block)
    m.connect(src_block.name, "out", integrator_block.name, "in")

    sim_cfg = SimulationConfig(dt, T, logging=[f"{integrator_block.name}.outputs.out"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs[f"{integrator_block.name}.outputs.out"]


# ----------------------------------------------------------------------
def test_integrator_scalar_forward():
    src = Step("src", start_time=0.1, value_before=0.0, value_after=1.0)
    I = DiscreteIntegrator("I", method="euler forward")

    logs = run_sim(src, I, dt=0.1, T=0.3)

    assert np.allclose(logs[0], [[0.0]])
    assert np.allclose(logs[1], [[0.0]])
    assert np.allclose(logs[2], [[0.1]])


# ----------------------------------------------------------------------
def test_integrator_vector_forward():
    src = Step(
        "src",
        start_time=0.1,
        value_before=[[0.0], [0.0]],
        value_after=[[1.0], [2.0]],
    )
    I = DiscreteIntegrator("I", method="euler forward")

    logs = run_sim(src, I, dt=0.1, T=0.3)

    assert np.allclose(logs[0], [[0.0], [0.0]])
    assert np.allclose(logs[1], [[0.0], [0.0]])
    assert np.allclose(logs[2], [[0.1], [0.2]])


# ----------------------------------------------------------------------
def test_integrator_matrix_forward():
    src = Step(
        "src",
        start_time=0.1,
        value_before=[[0.0, 0.0],
                      [0.0, 0.0]],
        value_after=[[1.0, 2.0],
                     [3.0, 4.0]],
    )
    I = DiscreteIntegrator("I", method="euler forward")

    logs = run_sim(src, I, dt=0.1, T=0.3)

    assert np.allclose(logs[0], np.zeros((2, 2)))
    assert np.allclose(logs[1], np.zeros((2, 2)))
    assert np.allclose(logs[2], 0.1 * np.array([[1.0, 2.0], [3.0, 4.0]]))


# ----------------------------------------------------------------------
def test_integrator_scalar_backward():
    src = Step("src", start_time=0.1, value_before=0.0, value_after=1.0)
    I = DiscreteIntegrator("I", method="euler backward")

    logs = run_sim(src, I, dt=0.1, T=0.3)

    assert np.allclose(logs[0], [[0.0]])
    assert np.allclose(logs[1], [[0.1]])
    assert np.allclose(logs[2], [[0.2]])


# ----------------------------------------------------------------------
def test_integrator_matrix_backward():
    src = Step(
        "src",
        start_time=0.1,
        value_before=[[0.0, 0.0],
                      [0.0, 0.0]],
        value_after=[[1.0, 2.0],
                     [3.0, 4.0]],
    )
    I = DiscreteIntegrator("I", method="euler backward")

    logs = run_sim(src, I, dt=0.1, T=0.3)

    expected1 = 0.1 * np.array([[1.0, 2.0], [3.0, 4.0]])
    expected2 = 0.2 * np.array([[1.0, 2.0], [3.0, 4.0]])

    assert np.allclose(logs[0], np.zeros((2, 2)))
    assert np.allclose(logs[1], expected1)
    assert np.allclose(logs[2], expected2)


# ----------------------------------------------------------------------
def test_integrator_initial_state():
    src = Step("src", start_time=0.1, value_before=0.0, value_after=1.0)
    I = DiscreteIntegrator("I", initial_state=[[5.0]], method="euler forward")

    logs = run_sim(src, I, dt=0.1, T=0.3)

    assert np.allclose(logs[0], [[5.0]])
    assert np.allclose(logs[1], [[5.0]])
    assert np.allclose(logs[2], [[5.1]])


# ----------------------------------------------------------------------
def test_integrator_missing_input():
    I = DiscreteIntegrator("I")
    m = Model()
    m.add_block(I)

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)
    sim.initialize()

    with pytest.raises(RuntimeError):
        sim.step()


# ----------------------------------------------------------------------
def test_integrator_input_shape_change_raises():
    # block-only: once shape known, it cannot change
    I = DiscreteIntegrator("I", method="euler forward")

    I.inputs["in"] = np.array([[0.0]])
    I.initialize(0.0)
    I.output_update(0.0, 0.1)
    I.state_update(0.0, 0.1)

    I.inputs["in"] = np.array([[1.0, 2.0],
                               [3.0, 4.0]])
    with pytest.raises(ValueError) as err:
        I.state_update(0.1, 0.1)
    assert "shape" in str(err.value)
