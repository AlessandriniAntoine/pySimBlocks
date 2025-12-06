import numpy as np

step_value_before = np.array([[0.0]])
step_value_after = np.array([[0.5]])
step_t_step = 0.2

sofa_scene_file = '/home/aalessan/Documents/ComplianceRobotics/emio/EmioLabs/assets/labs/EmioLabs_pySimBlocks/lab_pendulum.py'
sofa_input_keys = np.array(['u'])
sofa_output_keys = np.array(['markers', 'y'])

dt = 0.016666666666666666
T = 2.0