import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.sinusoidal import Sinusoidal
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.operators.zero_order_hold import ZeroOrderHold


def run_sim(src, block, dt=0.01, T=0.1):
    model = Model("test")
    model.add_block(src)
    model.add_block(block)
    model.connect(src.name, "out", block.name, "in")

    sim_cfg = SimulationConfig(dt, T, logging=[f"{block.name}.outputs.out"])
    sim = Simulator(model, sim_cfg)
    logs = sim.run()
    return logs[f"{block.name}.outputs.out"]


# ------------------------------------------------------------------

def test_zoh_passthrough_first_sample():
    src = Constant("src", 3.0)
    zoh = ZeroOrderHold("zoh", sample_time=0.1)

    logs = run_sim(src, zoh, dt=0.01, T=0.03)

    assert np.allclose(logs[0], [[3.0]])
    assert np.allclose(logs[1], [[3.0]])


# ------------------------------------------------------------------

def test_zoh_hold_behavior():
    """
    sample_time=0.05s, dt=0.01s -> update expected at k=0,5,10...
    We check:
      - values constant between k=0..4
      - change occurs at k=5 (very likely for sinusoidal)
    """
    src = Sinusoidal("src", amplitude=1.0, frequency=1.0, offset=0.0, phase=0.0)
    zoh = ZeroOrderHold("zoh", sample_time=0.05)

    logs = run_sim(src, zoh, dt=0.01, T=0.11)

    # held constant over [0..4]
    for k in range(1, 5):
        assert np.allclose(logs[k], logs[0])

    # at k=5, new sample should be taken (may still coincidentally match,
    # but extremely unlikely; we keep a strict "not allclose" check)
    assert not np.allclose(logs[5], logs[0])

    # held constant over [5..9]
    for k in range(6, 10):
        assert np.allclose(logs[k], logs[5])


# ------------------------------------------------------------------

def test_zoh_vector_signal():
    src = Constant("src", [[1.0], [2.0]])
    zoh = ZeroOrderHold("zoh", sample_time=0.05)

    logs = run_sim(src, zoh, dt=0.01, T=0.03)

    assert np.allclose(logs[0], [[1.0], [2.0]])


# ------------------------------------------------------------------

def test_zoh_matrix_signal():
    src = Constant("src", [[1.0, 2.0],
                           [3.0, 4.0]])
    zoh = ZeroOrderHold("zoh", sample_time=0.05)

    logs = run_sim(src, zoh, dt=0.01, T=0.03)

    assert np.allclose(logs[0], [[1.0, 2.0], [3.0, 4.0]])
    assert logs[0].shape == (2, 2)


# ------------------------------------------------------------------

def test_zoh_shape_change_raises():
    # block-only: ZOH must reject shape changes once initialized
    zoh = ZeroOrderHold("zoh", sample_time=0.05)

    zoh.inputs["in"] = np.array([[1.0]])  # (1,1)
    zoh.initialize(0.0)

    zoh.inputs["in"] = np.array([[1.0, 2.0],
                                 [3.0, 4.0]])  # (2,2)
    with pytest.raises(ValueError) as err:
        zoh.output_update(0.01, 0.01)

    assert "shape" in str(err.value).lower()


# ------------------------------------------------------------------

def test_zoh_invalid_sample_time():
    with pytest.raises(ValueError):
        ZeroOrderHold("zoh", sample_time=0.0)
