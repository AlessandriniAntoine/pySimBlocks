import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.step import Step
from pySimBlocks.blocks.operators.delay import Delay


# ------------------------------------------------------------
def run_sim(value_before, value_after, delay_block, dt=0.1):
    m = Model()

    src = Step("src", start_time=0.1, value_before=value_before, value_after=value_after)
    m.add_block(src)
    m.add_block(delay_block)
    m.connect("src", "out", delay_block.name, "in")

    sim_cfg = SimulationConfig(dt, 3*dt, logging=[f"{delay_block.name}.outputs.out"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs[f"{delay_block.name}.outputs.out"]


# ------------------------------------------------------------
def test_delay_scalar_1_step():
    d = Delay("D", num_delays=1)
    logs = run_sim([[0.0]], [[5.0]], d)

    # Step output:
    # t=0.0 → 0
    # t=0.1 → 5
    # Delay of 1 step means:
    # y[0] = input[-1] (→ initial fill = 0)
    # y[1] = input[0] = 0
    # y[2] = input[1] = 5

    assert np.allclose(logs[0], [[0.0]])
    assert np.allclose(logs[1], [[0.0]])
    assert np.allclose(logs[2], [[5.0]])


# ------------------------------------------------------------
def test_delay_scalar_2_steps():
    d = Delay("D", num_delays=2)
    logs = run_sim([[0.0]], [[1.0]], d)

    # Step input:
    # u[0] = 0
    # u[1] = 1
    # u[2] = 1
    #
    # With 2-step delay:
    # y[0] = 0  (buffer = [0,0])
    # y[1] = 0  (buffer = [0,0])
    # y[2] = u[0] = 0

    assert np.allclose(logs[0], [[0]])
    assert np.allclose(logs[1], [[0]])
    assert np.allclose(logs[2], [[0]])


# ------------------------------------------------------------
def test_delay_with_initial_output():
    d = Delay("D", num_delays=2, initial_output=[[7.0]])
    logs = run_sim([[0.0]], [[1.0]], d)

    assert np.allclose(logs[0], [[7.0]])


# ------------------------------------------------------------
def test_delay_dimension_mismatch_initial_output():
    with pytest.raises(ValueError):
        Delay("D", num_delays=1, initial_output=[[1, 2]])


# ------------------------------------------------------------
def test_delay_uninitialized_buffer_error():
    m = Model()
    d = Delay("D", num_delays=1)
    m.add_block(d)

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)

    with pytest.raises(RuntimeError):
        sim.run(T=0.1)

# ------------------------------------------------------------
def test_delay_vector_1_step():
    # 2-dimensional input
    value_before = [[0.0], [0.0]]
    value_after = [[5.0], [10.0]]

    d = Delay("D", num_delays=1)
    logs = run_sim(value_before, value_after, d)

    # Step output:
    # t=0.0 → [0; 0], t=0.1 → [5;10]

    # 1-step delay means:
    # y[0] = input[-1] → initial fill = [0;0]
    # y[1] = input[0]  → [0;0]
    # y[2] = input[1]  → [5;10]

    expected0 = np.array([[0.0], [0.0]])
    expected1 = np.array([[0.0], [0.0]])
    expected2 = np.array([[5.0], [10.0]])

    assert np.allclose(logs[0], expected0)
    assert np.allclose(logs[1], expected1)
    assert np.allclose(logs[2], expected2)
