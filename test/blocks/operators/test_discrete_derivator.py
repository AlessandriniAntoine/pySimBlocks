import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.step import Step
from pySimBlocks.blocks.operators.discrete_derivator import DiscreteDerivator


# ------------------------------------------------------------
def run_sim(src_block, der_block, dt=0.1, T=0.3, verbose=False):
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
    Step: u = 0,0,1,1 → with dt=0.1
    dy = (u[k] - u[k-1]) / dt → 0,0,(1-0)/0.1=10 , 0
    """
    src = Step("src", start_time=0.1, value_before=0., value_after=1.)
    D = DiscreteDerivator("D")

    logs = run_sim(src, D, dt=0.1, T=0.4)

    assert np.allclose(logs[0], [[0.0]])     # no prev → 0
    assert np.allclose(logs[1], [[10.0]])     # still no change
    assert np.allclose(logs[2], [[0.0]])    # (1 - 0)/0.1
    assert np.allclose(logs[3], [[0.0]])     # (1 - 1)/0.1


# ------------------------------------------------------------
def test_derivator_vector():
    src = Step(
        "src",
        start_time=0.1,
        value_before=[[0.],[0.]],
        value_after=[[2.],[4.]]
    )
    D = DiscreteDerivator("D")

    logs = run_sim(src, D, dt=0.1, T=0.3)

    # u0=[0,0], u1=[2,4] → dy = ([2,4]-[0,0])/0.1 = [20,40]
    assert np.allclose(logs[0], [[0.],[0.]])
    assert np.allclose(logs[1], [[20.],[40.]])
    assert np.allclose(logs[2], [[0.],[0.]])


# ------------------------------------------------------------
def test_derivator_initial_output():
    D = DiscreteDerivator("D", initial_output=[[5.0]])
    src = Step("src", start_time=0.0, value_before=[[0.]], value_after=[[1.]])

    logs = run_sim(src, D, dt=0.1, T=0.1, verbose=False)

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
