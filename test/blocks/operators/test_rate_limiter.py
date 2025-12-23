import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.step import Step
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.sources.ramp import Ramp
from pySimBlocks.blocks.operators.rate_limiter import RateLimiter


# ------------------------------------------------------------
# Helper
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
# 1) Passthrough when initial_output is NOT set
# ------------------------------------------------------------
def test_rate_limiter_passthrough_without_initial_output():
    """
    initial_output not provided → y(-1) = u(0)

    Step with start_time=0 → u(0)=10
    Output must be immediately equal to input.
    """
    src = Step("src", start_time=0.0, value_before=0.0, value_after=10.0)
    R = RateLimiter("R", rising_slope=1.0, falling_slope=-1.0)

    logs = run_sim(src, R, dt=0.1, T=0.2)

    assert np.allclose(logs[0], [[10.0]])
    assert np.allclose(logs[1], [[10.0]])


# ------------------------------------------------------------
# 2) Rate limiting with explicit initial_output
# ------------------------------------------------------------
def test_rate_limiter_scalar_with_initial_output():
    """
    initial_output defines y(-1) and is never overridden.

    u = 10 (constant)
    y(-1) = 0
    rising_slope = 1, dt = 0.1

    Expected:
        y(0) = 0
        y(1) = 0.1
        y(2) = 0.2
    """
    src = Constant("src", 10.0)
    R = RateLimiter(
        "R",
        rising_slope=1.0,
        falling_slope=-1.0,
        initial_output=0.0
    )

    logs = run_sim(src, R, dt=0.1, T=0.3)

    assert np.allclose(logs[0], [[0.1]])
    assert np.allclose(logs[1], [[0.2]])
    assert np.allclose(logs[2], [[0.3]])


# ------------------------------------------------------------
# 3) No active limitation when slope is admissible
# ------------------------------------------------------------
def test_rate_limiter_no_active_limitation():
    """
    Ramp slope = 0.5
    Rate limits = ±5 → no limitation
    """
    src = Ramp("src", slope=0.5, offset=1.0)
    R = RateLimiter("R", rising_slope=5.0, falling_slope=-5.0)

    logs = run_sim(src, R, dt=0.1, T=0.3)

    # Output must exactly match input evolution
    for k in range(1, len(logs)):
        assert np.allclose(logs[k] - logs[k-1], [[0.05]])


# ------------------------------------------------------------
# 4) Vector rate limiting
# ------------------------------------------------------------
def test_rate_limiter_vector():
    """
    Two channels with different slopes.
    initial_output explicitly set to zero vector.
    """
    src = Step(
        "src",
        start_time=0.0,
        value_before=[[0.0], [0.0]],
        value_after=[[4.0], [-4.0]]
    )

    R = RateLimiter(
        "R",
        rising_slope=[1.0, 0.5],
        falling_slope=[-1.0, -0.5],
        initial_output=[[0.0], [0.0]]
    )

    logs = run_sim(src, R, dt=0.1, T=0.2)

    # First step after transition
    # channel 0: +0.1
    # channel 1: -0.05
    assert np.allclose(logs[0], [[0.1], [-0.05]])
    assert np.allclose(logs[1], [[0.2], [-0.1]])
    assert np.allclose(logs[2], [[0.3], [-0.15]])


# ------------------------------------------------------------
# 5) Missing input must raise RuntimeError
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
# 6) Invalid slope signs
# ------------------------------------------------------------
def test_rate_limiter_invalid_slopes():
    with pytest.raises(ValueError):
        RateLimiter("R", rising_slope=-1.0, falling_slope=-1.0)

    with pytest.raises(ValueError):
        RateLimiter("R", rising_slope=1.0, falling_slope=1.0)
