from enum import IntEnum
from pathlib import Path

import numpy as np

from lmi import get_lmi_controller, get_lmi_observer


class ControlMode(IntEnum):
    OPEN_LOOP = 0
    STATE_FEEDBACK = 1

    @property
    def short(self) -> str:
        return {0: "OL", 1: "SF"}[int(self)]

    @property
    def label(self) -> str:
        return {
            0: "Open Loop",
            1: "State Feedback",
        }[int(self)]


data_path = Path(__file__).parent / "data"

nb_markers = 3

# ctr_data = np.load(data_path / "controller_order5_linear.npz")
# K = ctr_data["feedback_gain"]
# G = ctr_data["feedforward_gain"]

obs_data = np.load(data_path / "observer_order5_linear.npz")
# L = obs_data["observer_gain"]
A = obs_data["state_matrix"]
B = obs_data["input_matrix"]
C = obs_data["output_matrix"]

x0 = np.zeros((A.shape[0], 1))
Abar = np.block([
    [A, B],
    [np.zeros((B.shape[1], A.shape[1] + B.shape[1]))]
])
Bbar = np.block([
    [np.zeros((A.shape[0], B.shape[1]))],
    [np.eye(B.shape[1])]
])
Cbar = np.block([
    [C, np.zeros((C.shape[0], B.shape[1]))]
])
 
K, G = get_lmi_controller(Abar, Bbar, Cbar)
L = get_lmi_observer(A, C)

