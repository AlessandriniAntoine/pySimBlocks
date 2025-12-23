import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.step import Step
from pySimBlocks.blocks.operators.discrete_integrator import DiscreteIntegrator


# ----------------------------------------------------------------------
def run_sim(src_block, integrator_block, dt=0.1, T=0.3):
    """
    Helper function: builds model, runs simulation,
    returns logs of integrator output.
    """
    m = Model()
    m.add_block(src_block)
    m.add_block(integrator_block)
    m.connect(src_block.name, "out", integrator_block.name, "in")

    sim_cfg = SimulationConfig(dt, T, logging=[f"{integrator_block.name}.outputs.out"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs[f"{integrator_block.name}.outputs.out"]


# ----------------------------------------------------------------------
# 1. TEST FORWARD EULER — SCALAR
# ----------------------------------------------------------------------
def test_integrator_scalar_forward():
    """
    Simulink convention (forward rectangular):

        x[n] = x[n-1] + dt * u[n]
        y[n] = x[n]

    Step input:
        u(0) = 0
        u(1) = 1
        u(2) = 1

    dt = 0.1 → results:

        y(0) = 0
        y(1) = 0
        y(2) = 0.1
    """
    src = Step("src", start_time=0.1, value_before=0.0, value_after=1.0)
    I = DiscreteIntegrator("I", method="euler forward")

    logs = run_sim(src, I, dt=0.1, T=0.3)

    assert np.allclose(logs[0], [[0.0]])
    assert np.allclose(logs[1], [[0.0]])
    assert np.allclose(logs[2], [[0.1]])


# ----------------------------------------------------------------------
# 2. TEST FORWARD EULER — VECTOR
# ----------------------------------------------------------------------
def test_integrator_vector_forward():
    src = Step(
        "src",
        start_time=0.1,
        value_before=[[0.0], [0.0]],
        value_after=[[1.0], [2.0]]
    )

    I = DiscreteIntegrator("I", method="euler forward")

    logs = run_sim(src, I, dt=0.1, T=0.3)

    # Expected:
    # y[0] = [0, 0]
    # y[1] = [0, 0]
    # y[2] = [0.1, 0.2]
    assert np.allclose(logs[0], [[0.0], [0.0]])
    assert np.allclose(logs[1], [[0.0], [0.0]])
    assert np.allclose(logs[2], [[0.1], [0.2]])


# ----------------------------------------------------------------------
# 3. TEST BACKWARD EULER (implicit)
# ----------------------------------------------------------------------
def test_integrator_scalar_backward():
    """
    Backward Euler definition in your code:

        y[n] = x[n] + dt * u[n]
        x[n+1] = x[n] + dt * u[n]

    Step:
        u(0)=0, u(1)=1, dt=0.1

    Expected:
        y(0) = 0
        y(1) = x(1)+dt*u(1) = 0 + 0.1*1 = 0.1
        y(2) = x(2)+dt*u(2) = 0.1 + 0.1*1 = 0.2
    """
    src = Step("src", start_time=0.1, value_before=0., value_after=1.)
    I = DiscreteIntegrator("I", method="euler backward")

    logs = run_sim(src, I, dt=0.1, T=0.3)

    assert np.allclose(logs[0], [[0.0]])
    assert np.allclose(logs[1], [[0.1]])
    assert np.allclose(logs[2], [[0.2]])


# ----------------------------------------------------------------------
# 4. TEST INITIAL STATE
# ----------------------------------------------------------------------
def test_integrator_initial_state():
    src = Step("src", start_time=0.1, value_before=0., value_after=1.)
    I = DiscreteIntegrator("I", initial_state=[[5.0]])

    logs = run_sim(src, I, dt=0.1, T=0.3)

    # Expected:
    # y(0) = 5
    # y(1) = 5
    # y(2) = 5 + 0.1*1 = 5.1
    assert np.allclose(logs[0], [[5.0]])
    assert np.allclose(logs[1], [[5.0]])
    assert np.allclose(logs[2], [[5.1]])

# ----------------------------------------------------------------------
# 5. TEST MISSING INPUT
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
