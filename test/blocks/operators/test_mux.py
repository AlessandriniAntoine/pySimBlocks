import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.operators.mux import Mux


# ------------------------------------------------------------
def run_sim(values, mux):
    m = Model()

    const_blocks = []
    for i, val in enumerate(values):
        c = Constant(f"c{i+1}", val)
        m.add_block(c)
        const_blocks.append(c)

    m.add_block(mux)
    for i, c in enumerate(const_blocks):
        m.connect(c.name, "out", mux.name, f"in{i+1}")

    sim_cfg = SimulationConfig(0.1, 0.1, logging=[f"{mux.name}.outputs.out"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs[f"{mux.name}.outputs.out"][-1]


# ------------------------------------------------------------
def test_mux_basic_concatenation():
    mux = Mux("M", num_inputs=2)
    out = run_sim([[[1.0]], [[2.0]]], mux)
    assert np.allclose(out, [[1.0], [2.0]])


# ------------------------------------------------------------
def test_mux_multi_dimensional_inputs():
    mux = Mux("M", num_inputs=3)
    out = run_sim([
        [[1.0], [2.0]],
        [[3.0]],
        [[4.0], [5.0], [6.0]],
    ], mux)

    expected = np.array([[1], [2], [3], [4], [5], [6]], dtype=float)
    assert np.allclose(out, expected)


# ------------------------------------------------------------
def test_mux_missing_input():
    m = Model()
    c1 = Constant("c1", [[1.0]])
    mux = Mux("M", num_inputs=2)

    m.add_block(c1)
    m.add_block(mux)

    m.connect("c1", "out", "M", "in1")
    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)
    sim.initialize()
    with pytest.raises(RuntimeError):
        sim.run(T=0.1)


# ------------------------------------------------------------
def test_mux_invalid_shape():
    m = Model()
    c1 = Constant("c1", [[1.0]])
    mux = Mux("M", num_inputs=2)

    m.add_block(c1)
    m.add_block(mux)

    # Manually inject invalid shape
    mux.inputs["in2"] = np.array([[1.0, 2.0]])  # Not (n,1)

    m.connect("c1", "out", "M", "in1")

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)

    with pytest.raises(RuntimeError):
        sim.initialize()
    with pytest.raises(RuntimeError) as err:
        sim.initialize()
    assert "must be a column vector (n,1)" in str(err.value)
