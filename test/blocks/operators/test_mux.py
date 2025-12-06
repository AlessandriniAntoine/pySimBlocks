import numpy as np
import pytest

from pySimBlocks.core.model import Model
from pySimBlocks.core.simulator import Simulator
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

    # connections
    for i, c in enumerate(const_blocks):
        m.connect(c.name, "out", mux.name, f"in{i+1}")

    sim = Simulator(m, dt=0.1)
    logs = sim.run(T=0.1, variables_to_log=[f"{mux.name}.outputs.out"])
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

    m.connect("c1", "out", "M", "in1")  # in2 missing

    sim = Simulator(m, dt=0.1)
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

    sim = Simulator(m, dt=0.1)

    with pytest.raises(RuntimeError):
        sim.run(T=0.1)
