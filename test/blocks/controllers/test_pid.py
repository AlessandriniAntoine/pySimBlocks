# test/blocks/controllers/test_pid.py

import numpy as np
import pytest

from pySimBlocks.core import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources.constant import Constant
from pySimBlocks.blocks.sources.step import Step
from pySimBlocks.blocks.controllers.pid import Pid


# ------------------------------------------------------------
# Helper
# ------------------------------------------------------------
def run_sim(src_block, pid_block, dt=0.1, T=0.3):
    m = Model()
    m.add_block(src_block)
    m.add_block(pid_block)
    m.connect(src_block.name, "out", pid_block.name, "e")

    sim_cfg = SimulationConfig(dt, T, logging=[f"{pid_block.name}.outputs.u"])
    sim = Simulator(m, sim_cfg)
    logs = sim.run()
    return logs[f"{pid_block.name}.outputs.u"]


# ------------------------------------------------------------
# 1) P-only
# ------------------------------------------------------------
def test_pid_P_only_constant_error():
    # u = Kp * e
    src = Constant("e", 1.0)
    pid = Pid("pid", controller="P", Kp=2.0, Ki=0.0, Kd=0.0)

    logs = run_sim(src, pid, dt=0.1, T=0.2)

    assert np.allclose(logs[0], [[2.0]])
    assert np.allclose(logs[1], [[2.0]])


# ------------------------------------------------------------
# 2) I-only (Euler forward)
# ------------------------------------------------------------
def test_pid_I_only_forward_integrates_in_state_only():
    # Euler forward policy in your code:
    # output uses I = x_i
    # state update: x_i(k+1) = x_i(k) + Ki * e * dt
    src = Constant("e", 1.0)
    pid = Pid("pid", controller="I", Ki=1.0, integration_method="euler forward")

    logs = run_sim(src, pid, dt=0.1, T=0.4)

    # k=0: x_i=0 -> u=0
    # k=1: x_i=0.1 -> u=0.1
    # k=2: x_i=0.2 -> u=0.2
    # k=3: x_i=0.3 -> u=0.3
    assert np.allclose(logs[0], [[0.0]])
    assert np.allclose(logs[1], [[0.1]])
    assert np.allclose(logs[2], [[0.2]])
    assert np.allclose(logs[3], [[0.3]])


# ------------------------------------------------------------
# 3) I-only (Euler backward)
# ------------------------------------------------------------
def test_pid_I_only_backward_output_depends_on_current_error():
    # Euler backward policy in your code:
    # output uses I = x_i + Ki*e*dt
    src = Constant("e", 1.0)
    pid = Pid("pid", controller="I", Ki=1.0, integration_method="euler backward")

    logs = run_sim(src, pid, dt=0.1, T=0.4)

    # k=0: x_i=0 -> u=0.1
    # k=1: x_i=0.1 -> u=0.2
    # k=2: x_i=0.2 -> u=0.3
    # k=3: x_i=0.3 -> u=0.4
    assert np.allclose(logs[0], [[0.1]])
    assert np.allclose(logs[1], [[0.2]])
    assert np.allclose(logs[2], [[0.3]])
    assert np.allclose(logs[3], [[0.4]])


# ------------------------------------------------------------
# 4) D-only response to a step
# ------------------------------------------------------------
def test_pid_D_only_step_response():
    with pytest.raises(ValueError) as e:
        pid = Pid("pid", controller="D", Kd=1.0)

    assert "Invalid controller type 'D'" in str(e.value)



# ------------------------------------------------------------
# 5) PI (Euler forward)
# ------------------------------------------------------------
def test_pid_PI_forward():
    # u = Kp*e + x_i, with x_i integrating
    src = Constant("e", 1.0)
    pid = Pid("pid", controller="PI", Kp=2.0, Ki=1.0, integration_method="euler forward")

    logs = run_sim(src, pid, dt=0.1, T=0.4)

    # k=0: x_i=0   -> u=2.0
    # k=1: x_i=0.1 -> u=2.1
    # k=2: x_i=0.2 -> u=2.2
    # k=3: x_i=0.3 -> u=2.3
    assert np.allclose(logs[0], [[2.0]])
    assert np.allclose(logs[1], [[2.1]])
    assert np.allclose(logs[2], [[2.2]])
    assert np.allclose(logs[3], [[2.3]])


# ------------------------------------------------------------
# 6) Saturation clamps output
# ------------------------------------------------------------
def test_pid_saturation_upper_clamp():
    src = Constant("e", 1.0)
    pid = Pid("pid", controller="P", Kp=100.0, u_max=3.0)

    logs = run_sim(src, pid, dt=0.1, T=0.2)

    assert np.allclose(logs[0], [[3.0]])
    assert np.allclose(logs[1], [[3.0]])


# ------------------------------------------------------------
# 7) Missing input raises at run (output_update)
# ------------------------------------------------------------
def test_pid_missing_input_raises():
    pid = Pid("pid", controller="PID", Kp=1.0, Ki=1.0, Kd=1.0)

    m = Model()
    m.add_block(pid)

    sim_cfg = SimulationConfig(0.1, 0.1, logging=["pid.outputs.u"])
    sim = Simulator(m, sim_cfg)

    sim.initialize()

    with pytest.raises(RuntimeError):
        sim.run()
