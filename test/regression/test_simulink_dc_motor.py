import numpy as np
from pathlib import Path

from pySimBlocks import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import LinearStateSpace
from pySimBlocks.blocks.operators import Sum
from pySimBlocks.blocks.controllers import Pid


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _dc_motor_discrete_matrices(dt: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    DC motor discrete-time model used in the Simulink reference dataset.

    Parameters match the reference scripts:
        R=0.1, L=0.5, J=0.01, K=0.1, a=0.001
    """
    R = 0.1
    L = 0.5
    J = 0.01
    K = 0.1
    a = 0.001

    A = np.array([[1 - dt * R / L, -dt * K / L],
                  [dt * K / J, 1 - dt * a / J]])
    B = np.array([[dt / L], [0]])
    C = np.array([[0, 1]])
    return A, B, C


def _load_simulink_npz() -> dict[str, np.ndarray]:
    """
    Loads the reference dataset shipped in the repository.

    Expected location:
        tests/data/simulink/simulation.npz
    """
    data_path = Path(__file__).resolve().parent / "data" / "simulink" / "dc_motor.npz"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Simulink reference dataset not found: {data_path}\n"
            "Place simulation.npz under tests/data/simulink/ (or update this path)."
        )
    return dict(np.load(str(data_path)))


def _extract(logs: dict, key: str) -> np.ndarray:
    v = np.array(logs[key])
    return v.reshape(-1).astype(float)


def _assert_close(ref: np.ndarray, got: np.ndarray, *, atol: float, rtol: float, label: str):
    assert ref.shape == got.shape, f"{label}: shape mismatch ref={ref.shape} got={got.shape}"
    if not np.allclose(ref, got, atol=atol, rtol=rtol):
        err = np.linalg.norm(ref - got)
        mx = np.max(np.abs(ref - got))
        raise AssertionError(
            f"{label}: not close (atol={atol}, rtol={rtol}). "
            f"L2={err:.3e}, max_abs={mx:.3e}"
        )


# ---------------------------------------------------------------------
# Reference simulations (pySimBlocks)
# ---------------------------------------------------------------------

def _sim_openloop(A: np.ndarray, B: np.ndarray, C: np.ndarray, T: float, dt: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ref = Step("command", start_time=1.0, value_before=0.0, value_after=1.0)
    motor = LinearStateSpace("motor", A, B, C)

    model = Model("openloop")
    model.add_block(ref)
    model.add_block(motor)
    model.connect("command", "out", "motor", "u")

    sim_cfg = SimulationConfig(dt, T, logging=["command.outputs.out", "motor.outputs.y"])
    sim = Simulator(model, sim_cfg, verbose=False)
    logs = sim.run()

    t = _extract(logs, "time")
    u = _extract(logs, "command.outputs.out")
    w = _extract(logs, "motor.outputs.y")
    return t, u, w


def _sim_pi(A: np.ndarray, B: np.ndarray, C: np.ndarray, Kp: np.ndarray, Ki: np.ndarray, T: float, dt: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ref = Step("ref", start_time=1.0, value_before=0.0, value_after=1.0)
    motor = LinearStateSpace("motor", A, B, C)
    error = Sum("error", signs="+-")
    pid = Pid("pid", Kp=Kp, Ki=Ki, controller="PI")

    model = Model("pi")
    for b in [ref, motor, error, pid]:
        model.add_block(b)

    model.connect("ref", "out", "error", "in1")
    model.connect("motor", "y", "error", "in2")
    model.connect("error", "out", "pid", "e")
    model.connect("pid", "u", "motor", "u")

    sim_cfg = SimulationConfig(dt, T, logging=["ref.outputs.out", "motor.outputs.y", "pid.outputs.u"])
    sim = Simulator(model, sim_cfg, verbose=False)
    logs = sim.run()

    t = _extract(logs, "time")
    r = _extract(logs, "ref.outputs.out")
    w = _extract(logs, "motor.outputs.y")
    u = _extract(logs, "pid.outputs.u")
    return t, u, w, r


def _sim_pid(A: np.ndarray, B: np.ndarray, C: np.ndarray, Kp: np.ndarray, Ki: np.ndarray, Kd: np.ndarray,
             T: float, dt: float, integration_method: str | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ref = Step("ref", start_time=1.0, value_before=0.0, value_after=1.0)
    motor = LinearStateSpace("motor", A, B, C)
    error = Sum("error", signs="+-")

    if integration_method is None:
        pid = Pid("pid", Kp=Kp, Ki=Ki, Kd=Kd)
    else:
        pid = Pid("pid", Kp=Kp, Ki=Ki, Kd=Kd, integration_method=integration_method)

    model = Model("pid")
    for b in [ref, motor, error, pid]:
        model.add_block(b)

    model.connect("ref", "out", "error", "in1")
    model.connect("motor", "y", "error", "in2")
    model.connect("error", "out", "pid", "e")
    model.connect("pid", "u", "motor", "u")

    sim_cfg = SimulationConfig(dt, T, logging=["ref.outputs.out", "motor.outputs.y", "pid.outputs.u"])
    sim = Simulator(model, sim_cfg, verbose=False)
    logs = sim.run()

    t = _extract(logs, "time")
    r = _extract(logs, "ref.outputs.out")
    w = _extract(logs, "motor.outputs.y")
    u = _extract(logs, "pid.outputs.u")
    return t, u, w, r


# ---------------------------------------------------------------------
# Regression tests vs Simulink reference
# ---------------------------------------------------------------------
def test_regression_openloop_matches_simulink():
    data = _load_simulink_npz()

    dt = 0.1
    T = 30.0
    A, B, C = _dc_motor_discrete_matrices(dt)

    t, u, w = _sim_openloop(A, B, C, T, dt)

    _assert_close(data["time"].reshape(-1), t, atol=1e-12, rtol=1e-12, label="time")
    _assert_close(data["uol"].reshape(-1), u, atol=1e-12, rtol=1e-12, label="uol")
    _assert_close(data["wol"].reshape(-1), w, atol=1e-12, rtol=1e-12, label="wol")


def test_regression_pi_matches_simulink():
    data = _load_simulink_npz()

    dt = 0.1
    T = 30.0
    A, B, C = _dc_motor_discrete_matrices(dt)

    Kp = np.array([[0.001]])
    Ki = np.array([[0.02]])

    t, u, w, r = _sim_pi(A, B, C, Kp, Ki, T, dt)

    _assert_close(data["time"].reshape(-1), t, atol=1e-12, rtol=1e-12, label="time")
    _assert_close(data["r"].reshape(-1), r, atol=1e-12, rtol=1e-12, label="r (reference)")
    _assert_close(data["upi"].reshape(-1), u, atol=1e-12, rtol=1e-12, label="upi")
    _assert_close(data["wpi"].reshape(-1), w, atol=1e-12, rtol=1e-12, label="wpi")


def test_regression_pid_matches_simulink():
    data = _load_simulink_npz()

    dt = 0.1
    T = 30.0
    A, B, C = _dc_motor_discrete_matrices(dt)

    Kp = np.array([[0.001]])
    Ki = np.array([[0.02]])
    Kd = np.array([[0.01]])

    t, u, w, r = _sim_pid(A, B, C, Kp, Ki, Kd, T, dt)

    _assert_close(data["time"].reshape(-1), t, atol=1e-12, rtol=1e-12, label="time")
    _assert_close(data["r"].reshape(-1), r, atol=1e-12, rtol=1e-12, label="r (reference)")
    _assert_close(data["upid"].reshape(-1), u, atol=1e-12, rtol=1e-12, label="upid")
    _assert_close(data["wpid"].reshape(-1), w, atol=1e-12, rtol=1e-12, label="wpid")


def test_regression_pid_backward_euler_matches_simulink():
    data = _load_simulink_npz()

    dt = 0.1
    T = 30.0
    A, B, C = _dc_motor_discrete_matrices(dt)

    Kp = np.array([[0.001]])
    Ki = np.array([[0.02]])
    Kd = np.array([[0.01]])

    t, u, w, r = _sim_pid(A, B, C, Kp, Ki, Kd, T, dt, integration_method="euler backward")

    _assert_close(data["time"].reshape(-1), t, atol=1e-12, rtol=1e-12, label="time")
    _assert_close(data["r"].reshape(-1), r, atol=1e-12, rtol=1e-12, label="r (reference)")
    _assert_close(data["upid_backward"].reshape(-1), u, atol=1e-12, rtol=1e-12, label="upid_backward")
    _assert_close(data["wpid_backward"].reshape(-1), w, atol=1e-12, rtol=1e-12, label="wpid_backward")
