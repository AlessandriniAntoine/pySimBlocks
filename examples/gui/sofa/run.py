from model import sim, T, dt
import numpy as np
import matplotlib.pyplot as plt

logs = sim.run(T=T, variables_to_log=[
    'step.outputs.out',
    'sofa.outputs.measure',
    'sum.outputs.out',
])
print('Simulation complete.')

length = len(next(iter(logs.values())))
time = np.arange(0, T, dt)[:length]

plt.figure()
step_outputs_out = np.array(logs['step.outputs.out']).reshape(length, -1)
for i in range(step_outputs_out.shape[1]):
    plt.step(time, step_outputs_out[:, i], where='post', label='step_outputs_out'+str(i))
sofa_outputs_measure = np.array(logs['sofa.outputs.measure']).reshape(length, -1)
for i in range(sofa_outputs_measure.shape[1]):
    plt.step(time, sofa_outputs_measure[:, i], where='post', label='sofa_outputs_measure'+str(i))
plt.xlabel('Time [s]')
plt.ylabel('Values')
plt.title('Outputs')
plt.legend()
plt.grid()

plt.figure()
sum_outputs_out = np.array(logs['sum.outputs.out']).reshape(length, -1)
for i in range(sum_outputs_out.shape[1]):
    plt.step(time, sum_outputs_out[:, i], where='post', label='sum_outputs_out'+str(i))
plt.xlabel('Time [s]')
plt.ylabel('Values')
plt.title('Command')
plt.legend()
plt.grid()

plt.show()