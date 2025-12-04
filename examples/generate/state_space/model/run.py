from model import sim, T, dt
import numpy as np
import matplotlib.pyplot as plt

logs = sim.run(T=T, variables_to_log=[
    'delay.outputs.out',
    'ref.outputs.out',
    'plant.outputs.x',
])
print('Simulation complete.')

length = len(next(iter(logs.values())))
time = np.arange(0, T, dt)[:length]

plt.figure()
delay_outputs_out = np.array(logs['delay.outputs.out']).reshape(length, -1)
for i in range(delay_outputs_out.shape[1]):
    plt.step(time, delay_outputs_out[:, i], where='post', label='delay_outputs_out'+str(i))
plant_outputs_x = np.array(logs['plant.outputs.x']).reshape(length, -1)
for i in range(plant_outputs_x.shape[1]):
    plt.step(time, plant_outputs_x[:, i], where='post', label='plant_outputs_x'+str(i))
ref_outputs_out = np.array(logs['ref.outputs.out']).reshape(length, -1)
for i in range(ref_outputs_out.shape[1]):
    plt.step(time, ref_outputs_out[:, i], where='post', label='ref_outputs_out'+str(i))
plt.xlabel('Time [s]')
plt.ylabel('Values')
plt.title('System response')
plt.legend()
plt.grid()

plt.show()