import numpy as np
import pytest

from pySimBlocks.blocks.operators.demux import Demux
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.core import Model, SimulationConfig, Simulator


def run_sim(value, num_outputs):
    m = Model()

    c = Constant("c", value)
    dmx = Demux("D", num_outputs=num_outputs)

    m.add_block(c)
    m.add_block(dmx)
    m.connect("c", "out", "D", "in")

    logs = [f"D.outputs.out{i+1}" for i in range(num_outputs)]
    sim_cfg = SimulationConfig(0.1, 0.1, logging=logs)
    sim = Simulator(m, sim_cfg)
    data = sim.run()
    return [data[key][-1] for key in logs]


def test_demux_basic_column_vector():
    outputs = run_sim([[1.0], [2.0], [3.0]], num_outputs=3)
    assert np.allclose(outputs[0], [[1.0]])
    assert np.allclose(outputs[1], [[2.0]])
    assert np.allclose(outputs[2], [[3.0]])


def test_demux_equal_split_when_divisible():
    outputs = run_sim([[1.0], [2.0], [3.0], [4.0]], num_outputs=2)
    assert np.allclose(outputs[0], [[1.0], [2.0]])
    assert np.allclose(outputs[1], [[3.0], [4.0]])


def test_demux_remainder_split_rule():
    # n=5, p=3 => q=1, m=2
    # out1/out2 have 2 elems, out3 has 1 elem
    outputs = run_sim([[1.0], [2.0], [3.0], [4.0], [5.0]], num_outputs=3)
    assert np.allclose(outputs[0], [[1.0], [2.0]])
    assert np.allclose(outputs[1], [[3.0], [4.0]])
    assert np.allclose(outputs[2], [[5.0]])


def test_demux_invalid_parameter():
    with pytest.raises(ValueError) as err:
        Demux("D", num_outputs=0)
    assert "num_outputs must be a positive integer" in str(err.value)


def test_demux_missing_input_raises():
    m = Model()
    dmx = Demux("D", num_outputs=2)
    m.add_block(dmx)

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)

    with pytest.raises(RuntimeError) as err:
        sim.run(T=0.1)

    assert "not connected or not set" in str(err.value)


def test_demux_rejects_matrix_input():
    m = Model()
    c = Constant("c", [[1.0, 2.0], [3.0, 4.0]])
    dmx = Demux("D", num_outputs=4)

    m.add_block(c)
    m.add_block(dmx)
    m.connect("c", "out", "D", "in")

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)

    with pytest.raises(RuntimeError) as err:
        sim.run(T=0.1)

    assert "must be a column vector (n,1)" in str(err.value)


def test_demux_rejects_1d_input():
    dmx = Demux("D", num_outputs=1)
    dmx.inputs["in"] = np.array([5.0])

    with pytest.raises(ValueError) as err:
        dmx.output_update(t=0.0, dt=0.1)

    assert "must be a column vector (n,1)" in str(err.value)


def test_demux_rejects_more_outputs_than_input_length():
    m = Model()
    c = Constant("c", [[1.0], [2.0]])
    dmx = Demux("D", num_outputs=3)

    m.add_block(c)
    m.add_block(dmx)
    m.connect("c", "out", "D", "in")

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)

    with pytest.raises(RuntimeError) as err:
        sim.run(T=0.1)

    assert "must be <= input vector length" in str(err.value)
