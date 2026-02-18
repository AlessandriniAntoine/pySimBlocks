import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.step import Step
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.sources.ramp import Ramp
from pySimBlocks.blocks.operators.rate_limiter import RateLimiter


# ------------------------------------------------------------
def run_sim(src_block, rate_block, dt=0.1, T=0.3):
    m = Model()
    m.add_block(src_block)
    m.add_block(rate_block)
    m.connect(src_block.name, "out", rate_block.name, "in")

    sim_cfg = SimulationConfig(dt, T, logging=[f"{rate_block.name}.outputs.out"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs[f"{rate_block.name}.outputs.out"]


# ------------------------------------------------------------
def test_rate_limiter_passthrough_without_initial_output():
    src = Step("src", start_time=0.0, value_before=0.0, value_after=10.0)
    R = RateLimiter("R", rising_slope=1.0, falling_slope=-1.0)

    logs = run_sim(src, R, dt=0.1, T=0.2)

    assert np.allclose(logs[0], [[10.0]])
    assert np.allclose(logs[1], [[10.0]])


# ------------------------------------------------------------
def test_rate_limiter_scalar_with_initial_output():
    src = Constant("src", 10.0)
    R = RateLimiter("R", rising_slope=1.0, falling_slope=-1.0, initial_output=0.0)

    logs = run_sim(src, R, dt=0.1, T=0.3)

    assert np.allclose(logs[0], [[0.1]])
    assert np.allclose(logs[1], [[0.2]])
    assert np.allclose(logs[2], [[0.3]])


# ------------------------------------------------------------
def test_rate_limiter_no_active_limitation():
    src = Ramp("src", slope=0.5, offset=1.0)
    R = RateLimiter("R", rising_slope=5.0, falling_slope=-5.0)

    logs = run_sim(src, R, dt=0.1, T=0.3)

    for k in range(1, len(logs)):
        assert np.allclose(logs[k] - logs[k - 1], [[0.05]])


# ------------------------------------------------------------
def test_rate_limiter_vector():
    src = Step(
        "src",
        start_time=0.0,
        value_before=[[0.0], [0.0]],
        value_after=[[4.0], [-4.0]],
    )

    R = RateLimiter(
        "R",
        rising_slope=[1.0, 0.5],
        falling_slope=[-1.0, -0.5],
        initial_output=[[0.0], [0.0]],
    )

    logs = run_sim(src, R, dt=0.1, T=0.2)

    assert np.allclose(logs[0], [[0.1], [-0.05]])
    assert np.allclose(logs[1], [[0.2], [-0.1]])
    assert np.allclose(logs[2], [[0.3], [-0.15]])


# ------------------------------------------------------------
def test_rate_limiter_matrix_scalar_slopes():
    src = Step(
        "src",
        start_time=0.0,
        value_before=[[0.0, 0.0],
                      [0.0, 0.0]],
        value_after=[[10.0, -10.0],
                     [5.0,  -5.0]],
    )

    R = RateLimiter("R", rising_slope=1.0, falling_slope=-1.0, initial_output=0.0)

    logs = run_sim(src, R, dt=0.1, T=0.1)

    # dt=0.1, slopes +/-1 => max delta per step = +/-0.1 everywhere
    expected = np.array([[0.1, -0.1],
                         [0.1, -0.1]])
    assert np.allclose(logs[0], expected)


# ------------------------------------------------------------
def test_rate_limiter_matrix_vector_slopes_broadcast_columns():
    # input is (2,3)
    src = Step(
        "src",
        start_time=0.0,
        value_before=[[0.0, 0.0, 0.0],
                      [0.0, 0.0, 0.0]],
        value_after=[[10.0, -10.0, 2.0],
                     [5.0,   6.0, -7.0]],
    )

    # slopes as (2,1) via 1D -> (2,1); should broadcast across 3 columns
    R = RateLimiter(
        "R",
        rising_slope=[1.0, 0.5],
        falling_slope=[-1.0, -0.5],
        initial_output=0.0,
    )

    logs = run_sim(src, R, dt=0.1, T=0.1)

    # row1 limited to +/-0.1, row2 limited to +/-0.05
    expected = np.array([[0.1, -0.1, 0.1],
                         [0.05, 0.05, -0.05]])
    assert np.allclose(logs[0], expected)


# ------------------------------------------------------------
def test_rate_limiter_missing_input():
    R = RateLimiter("R", rising_slope=1.0, falling_slope=-1.0)
    m = Model()
    m.add_block(R)

    sim_cfg = SimulationConfig(0.1, 0.1)
    sim = Simulator(m, sim_cfg)

    with pytest.raises(RuntimeError):
        sim.initialize()


# ------------------------------------------------------------
def test_rate_limiter_invalid_slopes():
    with pytest.raises(ValueError):
        RateLimiter("R", rising_slope=-1.0, falling_slope=-1.0)

    with pytest.raises(ValueError):
        RateLimiter("R", rising_slope=1.0, falling_slope=1.0)


# ------------------------------------------------------------
def test_rate_limiter_input_shape_change_raises():
    # Direct block test: once initialized with (1,1), shape cannot change
    R = RateLimiter("R", rising_slope=1.0, falling_slope=-1.0, initial_output=0.0)

    R.inputs["in"] = np.array([[1.0]])
    R.initialize(0.0)
    R.output_update(0.0, 0.1)

    R.inputs["in"] = np.array([[1.0, 2.0],
                               [3.0, 4.0]])
    with pytest.raises(ValueError) as err:
        R.output_update(0.1, 0.1)

    assert "shape changed" in str(err.value) or "shape" in str(err.value)
