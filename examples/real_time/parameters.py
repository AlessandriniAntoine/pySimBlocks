from pathlib import Path
import numpy as np

data_path = Path(__file__).parent / "data"

ctr_data = np.load(data_path / "controller_order5_linear.npz")
K = ctr_data["feedback_gain"]
G = ctr_data["feedforward_gain"]

obs_data = np.load(data_path / "observer_order5_linear.npz")
L = obs_data["observer_gain"]
A = obs_data["state_matrix"]
B = obs_data["input_matrix"]
C = obs_data["output_matrix"]
