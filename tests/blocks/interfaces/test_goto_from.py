import numpy as np
import pytest

from pySimBlocks.core.model import Model
from pySimBlocks.core.config import SimulationConfig
from pySimBlocks.core.simulator import Simulator
from pySimBlocks.core import signal_bus
from pySimBlocks.blocks.interfaces.goto import Goto
from pySimBlocks.blocks.interfaces.bus_from import BusFrom
from pySimBlocks.blocks.sources.constant import Constant


def _run(model: Model, dt: float, T: float, logging: list[str]):
    cfg = SimulationConfig(dt=dt, T=T, t0=0.0, solver="fixed", logging=logging)
    sim = Simulator(model=model, sim_cfg=cfg, verbose=False)
    sim.run()
    return sim.logs


# --------------------------------------------------------------------------
# Unit tests: signal_bus module
# --------------------------------------------------------------------------

def test_signal_bus_reset():
    """reset() clears all entries from the bus."""
    signal_bus._signal_bus["foo"] = np.array([[1.0]])
    signal_bus.reset()
    assert signal_bus._signal_bus == {}


# --------------------------------------------------------------------------
# Unit tests: Goto block
# --------------------------------------------------------------------------

def test_goto_writes_to_bus():
    """Goto.output_update writes input value to the signal bus."""
    signal_bus.reset()
    g = Goto("g", tag="x")
    g.initialize(0.0)
    g.inputs["in"] = np.array([[3.0]])
    g.output_update(0.0, 0.01)
    assert np.allclose(signal_bus._signal_bus["x"], np.array([[3.0]]))


def test_goto_initialize_sets_none_when_no_input():
    """Goto.initialize stores None in the bus when no input is connected."""
    signal_bus.reset()
    g = Goto("g", tag="y")
    g.initialize(0.0)
    assert signal_bus._signal_bus["y"] is None


# --------------------------------------------------------------------------
# Unit tests: BusFrom block
# --------------------------------------------------------------------------

def test_bus_from_reads_from_bus():
    """BusFrom.output_update reads the value written by Goto."""
    signal_bus.reset()
    signal_bus._signal_bus["sig"] = np.array([[7.0]])
    f = BusFrom("f", tag="sig")
    f.initialize(0.0)
    f.output_update(0.0, 0.01)
    assert np.allclose(f.outputs["out"], np.array([[7.0]]))


def test_bus_from_raises_when_tag_missing():
    """BusFrom.output_update raises KeyError when the tag is absent from the bus."""
    signal_bus.reset()
    f = BusFrom("f", tag="missing_tag")
    with pytest.raises(KeyError, match="missing_tag"):
        f.output_update(0.0, 0.01)


def test_bus_from_initialize_returns_none_when_tag_absent():
    """BusFrom.initialize sets output to None if bus has no matching entry yet."""
    signal_bus.reset()
    f = BusFrom("f", tag="absent")
    f.initialize(0.0)
    assert f.outputs["out"] is None


# --------------------------------------------------------------------------
# Integration: BusFrom without matching Goto raises during simulation
# --------------------------------------------------------------------------

def test_bus_from_without_goto_raises():
    """A BusFrom block with no matching Goto raises during the first simulation step."""
    m = Model(name="orphan_bus_from")
    m.add_block(BusFrom("reader", tag="orphan"))

    cfg = SimulationConfig(dt=0.01, T=0.01, t0=0.0, solver="fixed", logging=[])
    sim = Simulator(model=m, sim_cfg=cfg, verbose=False)

    with pytest.raises((KeyError, RuntimeError)):
        sim.run()


# --------------------------------------------------------------------------
# Integration: basic Goto → BusFrom signal forwarding
# --------------------------------------------------------------------------

def test_goto_bus_from_basic_forwarding():
    """A signal published by Goto is correctly received by BusFrom in each tick."""
    m = Model(name="basic_fwd")
    m.add_block(Constant("src", value=5.0))
    m.add_block(Goto("writer", tag="shared"))
    m.add_block(BusFrom("reader", tag="shared"))
    m.connect("src", "out", "writer", "in")

    logs = _run(m, dt=0.01, T=0.05, logging=["reader.outputs.out"])
    values = np.array(logs["reader.outputs.out"]).flatten()
    assert np.allclose(values, 5.0)


# --------------------------------------------------------------------------
# Integration: execution order — BusFrom executes after Goto in same tick
# --------------------------------------------------------------------------

def test_execution_order_goto_before_bus_from():
    """build_execution_order places every Goto before its matching BusFrom."""
    m = Model(name="order_test")
    m.add_block(Constant("src", value=1.0))
    m.add_block(Goto("g", tag="t"))
    m.add_block(BusFrom("f", tag="t"))
    m.connect("src", "out", "g", "in")

    order = m.build_execution_order()
    names = [b.name for b in order]
    assert names.index("g") < names.index("f")


def test_execution_order_multiple_bus_froms():
    """All BusFrom blocks for the same tag are ordered after their Goto."""
    m = Model(name="multi_bus_from")
    m.add_block(Constant("src", value=2.0))
    m.add_block(Goto("g", tag="bus"))
    m.add_block(BusFrom("f1", tag="bus"))
    m.add_block(BusFrom("f2", tag="bus"))
    m.connect("src", "out", "g", "in")

    order = m.build_execution_order()
    names = [b.name for b in order]
    assert names.index("g") < names.index("f1")
    assert names.index("g") < names.index("f2")


# --------------------------------------------------------------------------
# Integration: bus isolation across runs (no bleed-over)
# --------------------------------------------------------------------------

def test_bus_reset_between_runs():
    """Two sequential runs with the same tag do not share bus state.

    Run 1 publishes value=1.0; run 2 publishes value=2.0.
    The BusFrom block must read 2.0 in run 2, not the stale 1.0 from run 1.
    """
    def make_model(value: float) -> Model:
        m = Model(name=f"model_{value}")
        m.add_block(Constant("src", value=value))
        m.add_block(Goto("writer", tag="shared_tag"))
        m.add_block(BusFrom("reader", tag="shared_tag"))
        m.connect("src", "out", "writer", "in")
        return m

    logs1 = _run(make_model(1.0), dt=0.01, T=0.01, logging=["reader.outputs.out"])
    logs2 = _run(make_model(2.0), dt=0.01, T=0.01, logging=["reader.outputs.out"])

    v1 = float(np.array(logs1["reader.outputs.out"]).flatten()[0])
    v2 = float(np.array(logs2["reader.outputs.out"]).flatten()[0])

    assert np.isclose(v1, 1.0)
    assert np.isclose(v2, 2.0)
