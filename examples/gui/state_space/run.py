import numpy as np
import matplotlib.pyplot as plt
from model import simulator, T, dt

logs = simulator.run(T=T, variables_to_log=[
    'C.outputs.out',
    'delay.outputs.out',
    'step.outputs.out',
    'plant.outputs.x',
    'plant.outputs.y',
])
print('Simulation complete.')

length = len(next(iter(logs.values())))
time = np.array(logs['time'])

plt.figure()
plant_outputs_x = np.array(logs['plant.outputs.x']).reshape(length, -1)
for i in range(plant_outputs_x.shape[1]):
    plt.step(time, plant_outputs_x[:, i], where='post', label='plant_outputs_x'+str(i))
delay_outputs_out = np.array(logs['delay.outputs.out']).reshape(length, -1)
for i in range(delay_outputs_out.shape[1]):
    plt.step(time, delay_outputs_out[:, i], where='post', label='delay_outputs_out'+str(i))
plt.xlabel('Time [s]')
plt.ylabel('Values')
plt.title('States')
plt.legend()
plt.grid()

plt.figure()
C_outputs_out = np.array(logs['C.outputs.out']).reshape(length, -1)
for i in range(C_outputs_out.shape[1]):
    plt.step(time, C_outputs_out[:, i], where='post', label='C_outputs_out'+str(i))
plant_outputs_y = np.array(logs['plant.outputs.y']).reshape(length, -1)
for i in range(plant_outputs_y.shape[1]):
    plt.step(time, plant_outputs_y[:, i], where='post', label='plant_outputs_y'+str(i))
plt.xlabel('Time [s]')
plt.ylabel('Values')
plt.title('Outputs')
plt.legend()
plt.grid()

plt.figure()
step_outputs_out = np.array(logs['step.outputs.out']).reshape(length, -1)
for i in range(step_outputs_out.shape[1]):
    plt.step(time, step_outputs_out[:, i], where='post', label='step_outputs_out'+str(i))
plt.xlabel('Time [s]')
plt.ylabel('Values')
plt.title('Command')
plt.legend()
plt.grid()

plt.show()