import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.step import Step
from pySimBlocks.blocks.operators.delay import Delay


# ------------------------------------------------------------
def run_sim(value_before, value_after, delay_block, dt=0.1, T_mult=3):
    m = Model()

    src = Step("src", start_time=0.1, value_before=value_before, value_after=value_after)
    m.add_block(src)
    m.add_block(delay_block)
    m.connect("src", "out", delay_block.name, "in")

    sim_cfg = SimulationConfig(dt, T_mult * dt, logging=[f"{delay_block.name}.outputs.out"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs[f"{delay_block.name}.outputs.out"]


# ------------------------------------------------------------
def test_delay_scalar_1_step():
    d = Delay("D", num_delays=1)
    logs = run_sim([[0.0]], [[5.0]], d)

    assert np.allclose(logs[0], [[0.0]])
    assert np.allclose(logs[1], [[0.0]])
    assert np.allclose(logs[2], [[5.0]])


# ------------------------------------------------------------
def test_delay_scalar_2_steps():
    d = Delay("D", num_delays=2)
    logs = run_sim([[0.0]], [[1.0]], d)

    assert np.allclose(logs[0], [[0.0]])
    assert np.allclose(logs[1], [[0.0]])
    assert np.allclose(logs[2], [[0.0]])


# ------------------------------------------------------------
def test_delay_with_initial_output_scalar():
    # initial_output scalar is allowed and should be used at t=0
    d = Delay("D", num_delays=2, initial_output=[[7.0]])
    logs = run_sim([[0.0]], [[1.0]], d)

    assert np.allclose(logs[0], [[7.0]])


# ------------------------------------------------------------
def test_delay_initial_output_scalar_broadcast_to_matrix():
    # initial_output scalar can be broadcast to match matrix input shape
    d = Delay("D", num_delays=1, initial_output=[[2.0]])

    value_before = [[0.0, 0.0],
                    [0.0, 0.0]]
    value_after = [[5.0, 6.0],
                   [7.0, 8.0]]

    logs = run_sim(value_before, value_after, d)

    # buffer at t=0 uses scalar init broadcasted to (2,2)
    assert np.allclose(logs[0], np.full((2, 2), 2.0))


# ------------------------------------------------------------
def test_delay_with_initial_output_matrix():
    init = [[1.0, 2.0],
            [3.0, 4.0]]
    d = Delay("D", num_delays=2, initial_output=init)

    value_before = init
    value_after = [[10.0, 20.0],
                   [30.0, 40.0]]

    logs = run_sim(value_before, value_after, d)

    assert np.allclose(logs[0], np.array(init))


# ------------------------------------------------------------
def test_delay_dimension_mismatch_initial_output_non_scalar_vs_input():
    # initial_output non-scalar fixes buffer shape; if input shape differs -> error
    d = Delay("D", num_delays=1, initial_output=[[1.0, 2.0]])  # shape (1,2)

    m = Model()
    src = Step("src", start_time=0.1, value_before=[[0.0], [0.0]], value_after=[[1.0], [1.0]])  # shape (2,1)
    m.add_block(src)
    m.add_block(d)
    m.connect("src", "out", "D", "in")

    sim_cfg = SimulationConfig(0.1, 0.2, logging=["D.outputs.out"])
    sim = Simulator(m, sim_cfg)

    with pytest.raises(ValueError) as err:
        sim.run()

    assert "shape" in str(err.value) and "expected" in str(err.value)


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
    value_before = [[0.0], [0.0]]
    value_after = [[5.0], [10.0]]

    d = Delay("D", num_delays=1)
    logs = run_sim(value_before, value_after, d)

    expected0 = np.array([[0.0], [0.0]])
    expected1 = np.array([[0.0], [0.0]])
    expected2 = np.array([[5.0], [10.0]])

    assert np.allclose(logs[0], expected0)
    assert np.allclose(logs[1], expected1)
    assert np.allclose(logs[2], expected2)


# ------------------------------------------------------------
def test_delay_matrix_1_step():
    value_before = [[0.0, 0.0],
                    [0.0, 0.0]]
    value_after = [[1.0, 2.0],
                   [3.0, 4.0]]

    d = Delay("D", num_delays=1)
    logs = run_sim(value_before, value_after, d)

    expected0 = np.array(value_before)
    expected1 = np.array(value_before)
    expected2 = np.array(value_after)

    assert np.allclose(logs[0], expected0)
    assert np.allclose(logs[1], expected1)
    assert np.allclose(logs[2], expected2)


# ------------------------------------------------------------
def test_delay_input_shape_change_over_time_raises():
    # First phase: scalar, second phase: matrix (shape change) -> should raise
    d = Delay("D", num_delays=1)

    d.initialize(0.0)
    d.inputs["in"] = np.array([[1.0]])  # scalar input
    d.output_update(0.0, 0.1)
    d.inputs["in"] = np.array([[1.0, 2.0],  # shape change to (2,2)
                             [3.0, 4.0]])
    with pytest.raises(ValueError) as err:
        d.state_update(0.1, 0.1)

    assert "shape" in str(err.value) and "expected" in str(err.value)
