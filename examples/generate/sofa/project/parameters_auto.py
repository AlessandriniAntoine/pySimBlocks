import numpy as np

step_value_before = np.array([[0]])
step_value_after = np.array([[8.0]])
step_start_time = 0.4

error_num_inputs = 2
error_signs = np.array([1.0, -1.0])

pid_controller = 'PI'
pid_Kp = np.array([[0.5]])
pid_Ki = np.array([[0.8]])

sofa_scene_file = '/home/aalessan/Documents/Perso/code/pySimBlocks/examples/generate/sofa/Finger.py'
sofa_input_keys = np.array(['cable'])
sofa_output_keys = np.array(['tip', 'measure'])

dt = 0.01
T = 5.0