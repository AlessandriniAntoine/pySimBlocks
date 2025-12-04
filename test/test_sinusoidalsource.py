import numpy as np

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks import Sinusoidal


def analytic_sinusoid(A, f, phi, offset, t):
    """
    A, f, phi, offset : (n,1)
    t : scalar
    return (n,1)
    """
    return A * np.sin(2 * np.pi * f * t + phi) + offset


def test_sinusoidal_1d():
    """
    Test Sinusoidal source in 1D against analytic reference.
    """
    A = np.array([[2.0]])
    f = np.array([[1.5]])     # Hz
    phi = np.array([[0.3]])
    offset = np.array([[1.0]])

    src = Sinusoidal(
        name="sin",
        amplitude=A,
        frequency=f,
        phase=phi,
        offset=offset,
    )

    model = Model("sin_test")
    model.add_block(src)

    dt = 0.01
    T = 2
    sim = Simulator(model, dt=dt)

    logs = sim.run(
        T=T,
        variables_to_log=["sin.outputs.out"]
    )

    y_sim = np.array(logs["sin.outputs.out"]).reshape(-1, 1)
    t_vals = np.arange(0, y_sim.shape[0])*dt

    # Compute reference
    y_ref = np.zeros_like(y_sim)
    for k, t in enumerate(t_vals):
        y_ref[k, 0] = (
            A * np.sin(2*np.pi*f*t + phi) + offset
        )[0, 0]

    err = np.linalg.norm(y_sim - y_ref)
    assert err < 1e-10, f"SinusoidalSource 1D failed: error={err}"


def test_sinusoidal_multi_dim():
    """
    Test 3-dimensional sinusoidal source with per-component parameters.
    """
    A = np.array([[1.0], [2.0], [0.5]])
    f = np.array([[1.0], [2.0], [3.0]])
    phi = np.array([[0.0], [0.5], [1.0]])
    offset = np.array([[0.0], [1.0], [-1.0]])

    src = Sinusoidal(
        name="sin3",
        amplitude=A,
        frequency=f,
        phase=phi,
        offset=offset,
    )

    model = Model("sin3_test")
    model.add_block(src)

    dt = 0.001
    T = 1.0
    sim = Simulator(model, dt=dt)

    logs = sim.run(
        T=T,
        variables_to_log=["sin3.outputs.out"]
    )

    length = len(logs["sin3.outputs.out"])
    y_sim = np.array(logs["sin3.outputs.out"]).reshape(length, -1)
    N = y_sim.shape[0]
    t_vals = np.arange(0, N)*dt

    # analytic
    y_ref = np.zeros_like(y_sim)
    for k, t in enumerate(t_vals):
        y_ref[k, :] = (
            A * np.sin(2*np.pi*f*t + phi) + offset
        ).reshape(-1)

    err = np.linalg.norm(y_sim - y_ref)
    assert err < 1e-10, f"Sinusoidal multi-dim failed: error={err}"


if __name__ == "__main__":
    test_sinusoidal_1d()
    test_sinusoidal_multi_dim()
    print("test_sinusoidal_ passed.")
