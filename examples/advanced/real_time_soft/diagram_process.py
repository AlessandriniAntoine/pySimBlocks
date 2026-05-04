"""DiagramProcess — exécute le schéma bloc pySimBlocks en temps réel.

Réécrit avec l'API RealTimeProcess. Plus de multiprocessing.Array/Event
gérés à la main : tout passe par self.shared et self.emit / @on.

Logique métier inchangée (select_cmd, filter_first_order, setup_motors,
send_motors_command).
"""

import time

import numpy as np
# from emioapi import EmioMotors

from pySimBlocks.real_time import RealTimeProcess, on


class EmioMotors:
    def __init__(self):
        self.position_p_gain = [0, 0, 0, 0]
        self.position_i_gain = [0, 0, 0, 0]
        self.position_d_gain = [0, 0, 0, 0]
        self.angles = [0, 0, 0, 0]

    def open(self):
        return True


class DiagramProcess(RealTimeProcess):
    listens = ["frame_ready", "measure_ready"]
 
    def setup(self):
        self._init_angles = np.array([0.7, 0, 0.7, 0])
        self._motors      = _setup_motors(self._init_angles)
        self._runner      = self.load_runner(
            input_blocks=["Camera", "Ref_cl", "Ref_ol", "Mode"],
            output_blocks=["Cmd"],
            target_dt=1 / 60,
        )
        self._command = np.zeros((2, 1))
        self._t       = time.perf_counter()
        self._dt      = 1 / 60
        self._first   = True
 
    @on("frame_ready")
    def send_command(self):
        _send_motors_command(self._motors, self._command, self._init_angles)
 
    @on("measure_ready")
    def control(self):
        if self._first:
            self._first = False
            self._t = time.perf_counter()
        else:
            t2 = time.perf_counter()
            self._dt = t2 - self._t
            self._t  = t2
 
        # --- LOCK GROUPÉ : un seul lock pour les 4 champs du tick ---
        s = self.shared.read("Camera", "Ref_cl", "Ref_ol", "Mode")
 
        outs = self._runner.tick(
            inputs={
                "Camera": s["Camera"].reshape(-1, 1),
                "Ref_cl": s["Ref_cl"].reshape(-1, 1),
                "Ref_ol": s["Ref_ol"].reshape(-1, 1),
                "Mode":   s["Mode"].reshape(1, 1),
            },
            dt=self._dt,
            pace=False,
        )


        print("--- Control step ---")
        print(f"Camera: {self.shared.Camera.flatten()}")
        print(f"Command: {self._command.flatten()}")
        print(f"dt: {self._dt*1000:.1f}ms")


# ---------------------------------------------------------------------------
# Hardware helpers (inchangés)
# ---------------------------------------------------------------------------

def _setup_motors(init_angles=None):
    if init_angles is None:
        init_angles = [0, 0, 0, 0]
    motors = EmioMotors()
    while not motors.open():
        print("Waiting for motors to open...")
        time.sleep(1)
    print("Motors opened successfully.")
    motors.position_p_gain = [2000, 800, 2000, 800]
    motors.position_i_gain = [0, 0, 0, 0]
    motors.position_d_gain = [50, 0, 50, 0]
    time.sleep(1)
    motors.angles = init_angles
    return motors


def _send_motors_command(motors, command, init_angles=None):
    if init_angles is None:
        init_angles = np.zeros(4)
    cmd = command.flatten()
    motors.angles = [
        cmd[0] + init_angles[0],
        init_angles[1],
        cmd[1] + init_angles[2],
        init_angles[3],
    ]


# ---------------------------------------------------------------------------
# Block diagram functions (référencées dans project.yaml — inchangées)
# ---------------------------------------------------------------------------

def select_cmd(t, dt, u_cl, u_ol, mode):
    try:
        mode = mode.item()
    except Exception:
        return {"u": np.zeros((2, 1))}

    if mode == 0:
        return {"u": u_ol}
    elif mode == 1:
        return {"u": u_cl}
    else:
        return {"u": np.zeros((2, 1))}


def filter_first_order(t, dt, u, u_prev):
    if dt <= 0:
        return {"u_filter": np.zeros((2, 1))}
    cutoff_freq = 30.0
    time_constant = 1 / (2 * np.pi * cutoff_freq)
    sampling_period = 1 / (1 / dt)
    alpha = sampling_period / (time_constant + sampling_period)
    return {"u_filter": alpha * u + (1 - alpha) * u_prev}
