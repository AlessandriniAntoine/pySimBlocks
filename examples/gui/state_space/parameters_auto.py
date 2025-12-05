import numpy as np

A_gain = np.array([[0.9, 0.4], [0.0, 0.97]])

B_gain = np.array([[0.0], [1.0]])

C_gain = np.array([[1.0, 0.0]])

delay_num_delays = 1
delay_initial_output = np.array([[0.0], [0.0]])

sum_num_inputs = 2
sum_signs = np.array([1, 1])

step_value_before = np.array([[0]])
step_value_after = np.array([[1]])
step_t_step = 0.5

plant_A = np.array([[0.9, 0.4], [0.0, 0.97]])
plant_B = np.array([[0.0], [1.0]])
plant_C = np.array([[1.0, 0.0]])
plant_x0 = np.array([[0.0], [0.0]])

dt = 0.01
T = 10.0