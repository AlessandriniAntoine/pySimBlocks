import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.operators.dead_zone import DeadZone


def run_sim(src, dz, dt=0.1, T=0.1):
    m = Model()
    m.add_block(src)
    m.add_block(dz)
    m.connect(src.name, "out", dz.name, "in")

    sim_cfg = SimulationConfig(dt, T, logging=[f"{dz.name}.outputs.out"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs[f"{dz.name}.outputs.out"]


def test_dead_zone_identity_default():
    src = Constant("src", 2.0)
    dz = DeadZone("dz")
    logs = run_sim(src, dz)
    assert np.allclose(logs[0], [[2.0]])


def test_dead_zone_inside_zone():
    src = Constant("src", 0.2)
    dz = DeadZone("dz", lower_bound=-0.5, upper_bound=0.5)
    logs = run_sim(src, dz)
    assert np.allclose(logs[0], [[0.0]])


def test_dead_zone_above():
    src = Constant("src", 2.0)
    dz = DeadZone("dz", lower_bound=-0.5, upper_bound=0.5)
    logs = run_sim(src, dz)
    assert np.allclose(logs[0], [[1.5]])


def test_dead_zone_below():
    src = Constant("src", -2.0)
    dz = DeadZone("dz", lower_bound=-0.5, upper_bound=0.5)
    logs = run_sim(src, dz)
    assert np.allclose(logs[0], [[-1.5]])


def test_dead_zone_vector():
    src = Constant("src", [[0.2], [1.0], [-1.0]])
    dz = DeadZone("dz", lower_bound=-0.3, upper_bound=0.3)
    logs = run_sim(src, dz)
    assert np.allclose(logs[0], [[0.0], [0.7], [-0.7]])


def test_dead_zone_matrix_scalar_bounds():
    src = Constant("src", [[0.2,  1.0],
                           [-1.0, 0.0]])
    dz = DeadZone("dz", lower_bound=-0.3, upper_bound=0.3)
    logs = run_sim(src, dz)

    # Apply component-wise:
    # 0.2 -> 0
    # 1.0 -> 1.0 - 0.3 = 0.7
    # -1.0 -> -1.0 - (-0.3) = -0.7
    # 0.0 -> 0
    expected = np.array([[0.0, 0.7],
                         [-0.7, 0.0]])
    assert np.allclose(logs[0], expected)


def test_dead_zone_matrix_vector_bounds_broadcast_columns():
    src = Constant("src", [[1.0, -1.0, 0.0],
                           [2.0, -2.0, 0.1]])  # (2,3)

    # (2,1) bounds via 1D -> broadcast on 3 cols
    dz = DeadZone("dz", lower_bound=[-0.5, -1.0], upper_bound=[0.5, 1.0])
    logs = run_sim(src, dz)

    # Row1 bounds [-0.5,0.5]:
    # [1.0 -> 0.5], [-1.0 -> -0.5], [0.0 -> 0]
    # Row2 bounds [-1,1]:
    # [2 -> 1], [-2 -> -1], [0.1 -> 0]
    expected = np.array([[0.5, -0.5, 0.0],
                         [1.0, -1.0, 0.0]])
    assert np.allclose(logs[0], expected)


def test_dead_zone_invalid_bounds():
    # Must include zero: lower <= 0 <= upper, and lower <= upper
    with pytest.raises(ValueError):
        dz = DeadZone("dz", lower_bound=1.0, upper_bound=0.0)
        dz.inputs["in"] = np.array([[0.0]])
        dz.initialize(0.0)


def test_dead_zone_missing_input():
    dz = DeadZone("dz")
    m = Model()
    m.add_block(dz)

    sim_cfg = SimulationConfig(0.1, 1.0)
    sim = Simulator(m, sim_cfg)

    with pytest.raises(RuntimeError):
        sim.initialize()
