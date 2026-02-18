# tests/blocks/observers/test_luenberger.py

import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.sources.step import Step
from pySimBlocks.blocks.observers.luenberger import Luenberger


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def run_sim(obs: Luenberger, u_src, y_src, dt=0.1, T=0.3, logging=None):
    m = Model()
    m.add_block(u_src)
    m.add_block(y_src)
    m.add_block(obs)

    m.connect(u_src.name, "out", obs.name, "u")
    m.connect(y_src.name, "out", obs.name, "y")

    if logging is None:
        logging = [
            f"{obs.name}.outputs.y_hat",
            f"{obs.name}.outputs.x_hat",
            f"{obs.name}.state.x_hat",
        ]

    sim_cfg = SimulationConfig(dt, T, logging=logging)
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs


def manual_observer_rollout(A, B, C, L, x0, u_seq, y_seq):
    """
    Returns:
        y_hat_seq: list of y_hat[k] = C x[k]
        x_next_seq: list of x[k+1]
    """
    x = x0.copy()
    y_hat_seq = []
    x_next_seq = []

    for (u, y) in zip(u_seq, y_seq):
        y_hat = C @ x
        x_next = A @ x + B @ u + L @ (y - y_hat)

        y_hat_seq.append(y_hat.copy())
        x_next_seq.append(x_next.copy())
        x = x_next

    return y_hat_seq, x_next_seq


# ------------------------------------------------------------
# 1) Basic correctness (state + output timing)
# ------------------------------------------------------------
def test_luenberger_basic_update_and_logging_timing():
    # Dimensions: n=2, m=1, p=1
    A = np.array([[0.9, 0.1],
                  [0.0, 0.95]], dtype=float)
    B = np.array([[0.1],
                  [0.05]], dtype=float)
    C = np.array([[1.0, 0.0]], dtype=float)
    L = np.array([[0.5],
                  [0.1]], dtype=float)

    obs = Luenberger("obs", A=A, B=B, C=C, L=L, x0=None)

    # Use constants so u[k] and y[k] are stable and easy to predict
    u_src = Constant("u_src", [[1.0]])     # u = 1
    y_src = Constant("y_src", [[0.0]])     # y = 0

    dt = 0.1
    T = 0.3  # 3 steps -> logs at k=0,1,2

    logs = run_sim(
        obs,
        u_src=u_src,
        y_src=y_src,
        dt=dt,
        T=T,
        logging=[
            "obs.outputs.y_hat",
            "obs.state.x_hat",
        ],
    )

    # Manual reference:
    # log index k corresponds to:
    #   - y_hat[k] computed from x[k]
    #   - state.x_hat already committed to x[k+1]
    x0 = np.zeros((2, 1), dtype=float)
    u_seq = [np.array([[1.0]]) for _ in range(3)]
    y_seq = [np.array([[0.0]]) for _ in range(3)]
    y_hat_ref, x_next_ref = manual_observer_rollout(A, B, C, L, x0, u_seq, y_seq)

    # outputs.y_hat
    assert np.allclose(logs["obs.outputs.y_hat"][0], y_hat_ref[0])
    assert np.allclose(logs["obs.outputs.y_hat"][1], y_hat_ref[1])
    assert np.allclose(logs["obs.outputs.y_hat"][2], y_hat_ref[2])

    # state.x_hat is x[k+1]
    assert np.allclose(logs["obs.state.x_hat"][0], x_next_ref[0])
    assert np.allclose(logs["obs.state.x_hat"][1], x_next_ref[1])
    assert np.allclose(logs["obs.state.x_hat"][2], x_next_ref[2])


# ------------------------------------------------------------
# 2) Provided x0 should be respected
# ------------------------------------------------------------
def test_luenberger_respects_x0():
    A = np.eye(2)
    B = np.zeros((2, 1))
    C = np.array([[1.0, 0.0]])
    L = np.zeros((2, 1))

    x0 = np.array([[2.0], [3.0]])
    obs = Luenberger("obs", A=A, B=B, C=C, L=L, x0=x0)

    u_src = Constant("u_src", [[0.0]])
    y_src = Constant("y_src", [[0.0]])

    logs = run_sim(
        obs,
        u_src=u_src,
        y_src=y_src,
        dt=0.1,
        T=0.1,
        logging=["obs.outputs.y_hat", "obs.state.x_hat"],
    )

    # At k=0: y_hat[0] = C x0 = 2
    assert np.allclose(logs["obs.outputs.y_hat"][0], [[2.0]])
    # state after first step is x1 = A x0 = x0 (since everything else is zero)
    assert np.allclose(logs["obs.state.x_hat"][0], x0)


# ------------------------------------------------------------
# 3) Missing inputs should raise (at runtime state_update)
# ------------------------------------------------------------
def test_luenberger_missing_u_raises():
    A = np.eye(1)
    B = np.ones((1, 1))
    C = np.ones((1, 1))
    L = np.ones((1, 1))

    obs = Luenberger("obs", A=A, B=B, C=C, L=L)
    y_src = Constant("y_src", [[0.0]])

    m = Model()
    m.add_block(y_src)
    m.add_block(obs)
    # only connect y
    m.connect("y_src", "out", "obs", "y")

    sim = Simulator(m, SimulationConfig(0.1, 0.1, logging=["obs.outputs.y_hat"]))
    sim.initialize()
    with pytest.raises(RuntimeError, match="Input 'u'"):
        sim.step()


def test_luenberger_missing_y_raises():
    A = np.eye(1)
    B = np.ones((1, 1))
    C = np.ones((1, 1))
    L = np.ones((1, 1))

    obs = Luenberger("obs", A=A, B=B, C=C, L=L)
    u_src = Constant("u_src", [[0.0]])

    m = Model()
    m.add_block(u_src)
    m.add_block(obs)
    # only connect u
    m.connect("u_src", "out", "obs", "u")

    sim = Simulator(m, SimulationConfig(0.1, 0.1, logging=["obs.outputs.y_hat"]))
    sim.initialize()
    with pytest.raises(RuntimeError, match="Input 'y'"):
        sim.step()


# ------------------------------------------------------------
# 4) Invalid matrix dimensions should raise at construction
# ------------------------------------------------------------
def test_luenberger_invalid_dimensions():
    A = np.eye(2)
    B = np.ones((3, 1))      # wrong rows
    C = np.ones((1, 2))
    L = np.ones((2, 1))

    with pytest.raises(ValueError):
        Luenberger("obs", A=A, B=B, C=C, L=L)


# ------------------------------------------------------------
# 5) Bad input shape (wrong number of elements) triggers reshape error
# ------------------------------------------------------------
def test_luenberger_bad_input_size_raises_value_error():
    A = np.eye(2)
    B = np.ones((2, 1))
    C = np.ones((1, 2))
    L = np.ones((2, 1))
    obs = Luenberger("obs", A=A, B=B, C=C, L=L)

    # u must be (1,1) -> OK, y must be (1,1) -> but we provide 2 elements
    u_src = Constant("u_src", [[0.0]])
    y_src = Constant("y_src", [[1.0], [2.0]])  # wrong total size for (1,1)

    m = Model()
    m.add_block(u_src)
    m.add_block(y_src)
    m.add_block(obs)
    m.connect("u_src", "out", "obs", "u")
    m.connect("y_src", "out", "obs", "y")

    sim = Simulator(m, SimulationConfig(0.1, 0.1, logging=["obs.outputs.y_hat"]))
    sim.initialize()
    with pytest.raises(ValueError):
        sim.step()

