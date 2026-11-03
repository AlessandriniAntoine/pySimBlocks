import sys

import numpy as np
import pytest

from pySimBlocks import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources import Constant
from pySimBlocks.blocks.systems import TransferFunction


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def _reference_response(num, den, u):
    """Independent difference-equation reference for H(z) = num/den.

    y[k] = sum_i b_i u[k-i] - sum_{i>=1} a_i y[k-i], with x0 = 0.
    """
    num = np.asarray(num, dtype=float)
    den = np.asarray(den, dtype=float)
    n = den.size
    b = np.zeros(n)
    b[-num.size:] = num
    b = b / den[0]
    a = den / den[0]

    y = np.zeros(len(u))
    for k in range(len(u)):
        acc = 0.0
        for i in range(n):
            if k - i >= 0:
                acc += b[i] * u[k - i]
        for i in range(1, n):
            if k - i >= 0:
                acc -= a[i] * y[k - i]
        y[k] = acc
    return y


def _simulate(tf, dt, T, u_value=1.0):
    """Run `tf` driven by a constant input and return the logged output y."""
    model = Model("tf_test")
    model.add_block(Constant("u", value=u_value))
    model.add_block(tf)
    model.connect("u", "out", tf.name, "u")

    sim = Simulator(model, SimulationConfig(dt=dt, T=T))
    key = f"{tf.name}.outputs.y"
    logs = sim.run(logging=[key])

    y = np.asarray(logs[key], dtype=float)
    return y.reshape(len(y), -1)[:, 0]


def _dc_gain(tf):
    """DC gain of the discretized system, H_d(z=1)."""
    n = tf.A.shape[0]
    return (tf.C @ np.linalg.solve(np.eye(n) - tf.A, tf.B) + tf.D).item()


# ------------------------------------------------------------------------------
# Discrete domain
# ------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "num, den",
    [
        ([0.5], [1.0, -0.9]),             # first order, strictly proper
        ([1.0, 0.5], [1.0, -0.5]),        # biproper (direct feedthrough)
        ([1.0, 2.0], [1.0, -1.2, 0.5]),   # second order
        ([3.0], [2.0]),                   # pure gain
        ([2.0, -1.8], [2.0, -1.0]),       # non-monic denominator
    ],
)
def test_discrete_step_response_matches_difference_equation(num, den):
    tf = TransferFunction("tf", num=num, den=den, domain="discrete")

    y = _simulate(tf, dt=0.1, T=3.0)

    expected = _reference_response(num, den, np.ones(len(y)))
    np.testing.assert_allclose(y, expected, atol=1e-10)


def test_discrete_initial_state_is_used():
    tf = TransferFunction(
        "tf", num=[0.5], den=[1.0, -0.9], domain="discrete", x0=[[2.0]]
    )

    y = _simulate(tf, dt=0.1, T=1.0, u_value=0.0)

    # C = 0.5, A = 0.9, x0 = 2  ->  y[k] = 0.5 * 2 * 0.9**k
    expected = 0.9 ** np.arange(len(y))
    np.testing.assert_allclose(y, expected, atol=1e-12)


def test_non_monic_denominator_is_normalized():
    monic = TransferFunction("a", num=[1.0], den=[1.0, -0.9])
    scaled = TransferFunction("b", num=[2.0], den=[2.0, -1.8])

    np.testing.assert_allclose(scaled.A, monic.A)
    np.testing.assert_allclose(scaled.B, monic.B)
    np.testing.assert_allclose(scaled.C, monic.C)
    np.testing.assert_allclose(scaled.D, monic.D)


def test_x0_accepts_1d_input():
    tf = TransferFunction(
        "tf", num=[1.0, 2.0], den=[1.0, -1.2, 0.5], domain="discrete", x0=[1.0, 2.0]
    )

    assert tf.state["x"].shape == (2, 1)
    np.testing.assert_allclose(tf.state["x"][:, 0], [1.0, 2.0])


# ------------------------------------------------------------------------------
# direct_feedthrough (needed before sample times are resolved)
# ------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "kwargs, expected",
    [
        (dict(num=[0.5], den=[1.0, -0.9]), False),
        (dict(num=[1.0, 0.5], den=[1.0, -0.5]), True),
        (dict(num=[3.0], den=[2.0]), True),
        (dict(num=[1.0], den=[1.0, 1.0], domain="continuous", discretization="tustin"), True),
        (dict(num=[1.0], den=[1.0, 1.0], domain="continuous", discretization="zoh"), False),
        (dict(num=[1.0, 1.0], den=[1.0, 2.0], domain="continuous", discretization="zoh"), True),
    ],
)
def test_direct_feedthrough_flag(kwargs, expected):
    tf = TransferFunction("tf", **kwargs)

    assert tf.direct_feedthrough is expected


# ------------------------------------------------------------------------------
# Continuous domain
# ------------------------------------------------------------------------------

def test_tustin_maps_pole_as_expected():
    Ts = 0.1
    tf = TransferFunction(
        "tf", num=[1.0], den=[1.0, 2.0], domain="continuous",
        discretization="tustin", sample_time=Ts,
    )
    tf.initialize(0.0)

    expected_pole = (1 - 2 * Ts / 2) / (1 + 2 * Ts / 2)
    assert tf.A.shape == (1, 1)
    assert tf.A[0, 0] == pytest.approx(expected_pole)


@pytest.mark.parametrize("method", ["tustin", "zoh"])
def test_discretization_preserves_dc_gain(method):
    if method == "zoh":
        pytest.importorskip("scipy")

    # H(s) = (2s + 3) / (s^2 + 4s + 5),  H(0) = 0.6
    tf = TransferFunction(
        "tf", num=[2.0, 3.0], den=[1.0, 4.0, 5.0], domain="continuous",
        discretization=method, sample_time=0.05,
    )
    tf.initialize(0.0)

    assert _dc_gain(tf) == pytest.approx(0.6)


@pytest.mark.parametrize("method", ["tustin", "zoh"])
def test_continuous_uses_global_dt_when_no_sample_time(method):
    if method == "zoh":
        pytest.importorskip("scipy")

    # H(s) = 1 / (s + 1): step response converges to 1.
    tf = TransferFunction(
        "tf", num=[1.0], den=[1.0, 1.0], domain="continuous", discretization=method
    )

    y = _simulate(tf, dt=0.1, T=10.0)

    assert y[-1] == pytest.approx(1.0, rel=1e-3)


def test_zoh_matches_exact_sampled_step_response():
    pytest.importorskip("scipy")
    dt = 0.1
    tf = TransferFunction(
        "tf", num=[1.0], den=[1.0, 1.0], domain="continuous", discretization="zoh"
    )

    y = _simulate(tf, dt=dt, T=3.0)

    expected = 1.0 - np.exp(-dt * np.arange(len(y)))
    np.testing.assert_allclose(y, expected, atol=1e-10)


def test_continuous_without_resolvable_period_raises():
    tf = TransferFunction("tf", num=[1.0], den=[1.0, 1.0], domain="continuous")

    with pytest.raises(RuntimeError):
        tf.initialize(0.0)


def test_zoh_without_scipy_raises_import_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "scipy", None)
    monkeypatch.setitem(sys.modules, "scipy.signal", None)
    tf = TransferFunction(
        "tf", num=[1.0], den=[1.0, 1.0], domain="continuous",
        discretization="zoh", sample_time=0.1,
    )

    with pytest.raises(ImportError):
        tf.initialize(0.0)


# ------------------------------------------------------------------------------
# Invalid arguments
# ------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "kwargs",
    [
        dict(num=[1.0], den=[0.0]),                          # zero denominator
        dict(num=[1.0, 2.0, 3.0], den=[1.0, 1.0]),           # improper
        dict(num=[1.0], den=[1.0, 1.0], domain="laplace"),   # bad domain
        dict(num=[1.0], den=[1.0, 1.0], discretization="euler"),
        dict(num=[1.0], den=[1.0, -0.5, 0.1], x0=[1.0, 2.0, 3.0]),  # bad x0 size
    ],
)
def test_invalid_arguments_raise_value_error(kwargs):
    with pytest.raises(ValueError):
        TransferFunction("tf", **kwargs)
