import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources import Sinusoidal, Constant
from pySimBlocks.blocks.operators import ZeroOrderHold


def run_sim(src, block, dt=0.01, T=0.1):
    model = Model("test")
    model.add_block(src)
    model.add_block(block)
    model.connect(src.name, "out", block.name, "in")

    sim_cfg = SimulationConfig(dt, T, logging=[f"{block.name}.outputs.out"])
    sim = Simulator(model, sim_cfg)
    sim.initialize()

    logs = sim.run()
    return logs[f"{block.name}.outputs.out"]


# ------------------------------------------------------------------

def test_zoh_passthrough_first_sample():
    """
    initial_output absent -> y(-1) = u(0)
    """
    src = Constant("src", 3.0)
    zoh = ZeroOrderHold("zoh", sample_time=0.1)

    logs = run_sim(src, zoh, dt=0.01, T=0.03)

    assert np.allclose(logs[0], [[3.0]])
    assert np.allclose(logs[1], [[3.0]])


# ------------------------------------------------------------------

def test_zoh_hold_behavior():
    """
    Signal sampled every 0.05s, simulator dt = 0.01s
    """
    src = Sinusoidal("src", amplitude=1.0, frequency=1.0)
    zoh = ZeroOrderHold("zoh", sample_time=0.05)

    logs = run_sim(src, zoh, dt=0.01, T=0.11)

    # Samples should update at k = 0, 5, 10
    assert np.allclose(logs[0], logs[1])
    assert np.allclose(logs[1], logs[4])
    assert not np.allclose(logs[4], logs[5])



# ------------------------------------------------------------------

def test_zoh_vector_signal():
    src = Constant("src", [[1.0], [2.0]])
    zoh = ZeroOrderHold("zoh", sample_time=0.05)

    logs = run_sim(src, zoh, dt=0.01, T=0.03)

    assert np.allclose(logs[0], [[1.0], [2.0]])


# ------------------------------------------------------------------

def test_zoh_invalid_sample_time():
    with pytest.raises(ValueError):
        ZeroOrderHold("zoh", sample_time=0.0)
