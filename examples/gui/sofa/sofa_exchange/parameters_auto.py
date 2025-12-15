import numpy as np

pid_controller = 'PI'
pid_Kp = np.array([[0.5]])
pid_Ki = np.array([[0.8]])

step_value_before = np.array([[0.0]])
step_value_after = np.array([[15.0]])
step_start_time = 0.5

error_num_inputs = 2
error_signs = np.array([1.0, -1.0])

sofa_input_keys = np.array(['cable'])
sofa_output_keys = np.array(['measure'])
sofa_scene_file = '/home/aalessan/Documents/Perso/code/pySimBlocks/examples/gui/sofa/sofa_exchange/Finger.py'

dt = 0.01
T = 8.0