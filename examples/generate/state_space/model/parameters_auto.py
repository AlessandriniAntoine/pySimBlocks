import numpy as np

ref_value_before = np.array([0])
ref_value_after = np.array([1])
ref_t_step = 0.5

B_gain = np.array([[1.0]])

sum_signs = np.array([1, 1])

delay_initial_output = np.array([0])

A_gain = np.array([[0.9]])

plant_A = np.array([[0.9]])
plant_B = np.array([[1]])
plant_C = np.array([[1]])
plant_x0 = np.array([[0]])

dt = 0.1
T = 3.0