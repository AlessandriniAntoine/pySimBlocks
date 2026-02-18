import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.step import Step
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.operators.discrete_integrator import DiscreteIntegrator


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
# 1) FORWARD EULER — SCALAR
# ----------------------------------------------------------------------
def test_integrator_scalar_forward():
    src = Step("src", start_time=0.1, value_before=0.0, value_after=1.0)
    I = DiscreteIntegrator("I", method="euler forward")

    logs = run_sim(src, I, dt=0.1, T=0.3)

    # forward: y[k] = x[k], x[k+1] = x[k] + dt*u[k]
    # u: 0,1,1 -> y: 0,0,0.1
    assert np.allclose(logs[0], [[0.0]])
    assert np.allclose(logs[1], [[0.0]])
    assert np.allclose(logs[2], [[0.1]])


# ----------------------------------------------------------------------
# 2) FORWARD EULER — VECTOR
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
# 3) BACKWARD EULER — SCALAR
# ----------------------------------------------------------------------
def test_integrator_scalar_backward():
    src = Step("src", start_time=0.1, value_before=0.0, value_after=1.0)
    I = DiscreteIntegrator("I", method="euler backward")

    logs = run_sim(src, I, dt=0.1, T=0.3)

    # backward output: y = x + dt*u (with x updated in state_update)
    # u: 0,1,1
    # y0 = 0 + 0.1*0 = 0
    # y1 = 0 + 0.1*1 = 0.1
    # y2 = 0.1 + 0.1*1 = 0.2
    assert np.allclose(logs[0], [[0.0]])
    assert np.allclose(logs[1], [[0.1]])
    assert np.allclose(logs[2], [[0.2]])


# ----------------------------------------------------------------------
# 4) INITIAL STATE — FREEZES SHAPE (NON-SCALAR)
# ----------------------------------------------------------------------
def test_integrator_initial_state_matrix_freezes_shape():
    src = Constant("src", [[1.0, 2.0], [3.0, 4.0]])
    I = DiscreteIntegrator("I", initial_state=np.zeros((2, 2)), method="euler forward")

    logs = run_sim(src, I, dt=0.1, T=0.2)

    # forward: y = x, with x0 fixed
    assert np.allclose(logs[0], np.zeros((2, 2)))
    assert np.allclose(logs[1], 0.1 * np.array([[1.0, 2.0], [3.0, 4.0]]))


# ----------------------------------------------------------------------
# 5) PLACEHOLDER (1,1) MUST NOT FREEZE; UPGRADE ON FIRST NON-SCALAR
# ----------------------------------------------------------------------
def test_integrator_placeholder_upgrades_to_matrix_on_first_non_scalar_input():
    # Step goes from scalar -> matrix; scalar should NOT freeze the integrator if no initial_state
    src = Step(
        "src",
        start_time=0.1,
        value_before=[[0.0]],  # scalar placeholder
        value_after=[[1.0, 2.0], [3.0, 4.0]],  # matrix
    )
    I = DiscreteIntegrator("I", method="euler forward")

    logs = run_sim(src, I, dt=0.1, T=0.3)

    # At t=0: output placeholder (1,1) is fine
    assert np.allclose(logs[0], [[0.0]])

    # After step: integrator should upgrade and integrate matrix
    # forward y1 is still x0 (after upgrade, still zero matrix)
    # y2 is dt*u1
    assert logs[1].shape == (2, 2)
    assert np.allclose(logs[1], np.zeros((2, 2)))
    assert np.allclose(logs[2], 0.1 * np.array([[1.0, 2.0], [3.0, 4.0]]))


# ----------------------------------------------------------------------
# 6) SHAPE CHANGE AFTER FREEZE MUST RAISE
# ----------------------------------------------------------------------
def test_integrator_shape_change_after_freeze_raises():
    # Freeze to (2,2) via initial_state, then feed (3,1)
    src = Constant("src", [[1.0], [2.0], [3.0]])
    I = DiscreteIntegrator("I", initial_state=np.zeros((2, 2)), method="euler backward")

    m = Model()
    m.add_block(src)
    m.add_block(I)
    m.connect("src", "out", "I", "in")

    sim_cfg = SimulationConfig(0.1, 0.2, logging=["I.outputs.out"])
    sim = Simulator(m, sim_cfg)

    with pytest.raises(ValueError) as err:
        sim.run()

    assert "shape" in str(err.value).lower()


# ----------------------------------------------------------------------
# 7) SCALAR INPUT (1,1) MUST BROADCAST WHEN SHAPE IS FROZEN TO MATRIX
# ----------------------------------------------------------------------
def test_integrator_scalar_broadcast_into_frozen_matrix_shape():
    src = Constant("src", [[2.0]])  # scalar (1,1)
    I = DiscreteIntegrator("I", initial_state=np.zeros((2, 2)), method="euler backward")

    logs = run_sim(src, I, dt=0.1, T=0.2)

    # backward: y = x + dt*u, with u broadcast to 2x2
    assert logs[0].shape == (2, 2)
    assert np.allclose(logs[0], 0.1 * 2.0 * np.ones((2, 2)))
