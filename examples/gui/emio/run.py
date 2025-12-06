from model import sim, T, dt
import numpy as np
import matplotlib.pyplot as plt

logs = sim.run(T=T, variables_to_log=[
    'step.outputs.out',
    'sofa.outputs.markers',
    'sofa.outputs.y',
])
print('Simulation complete.')

length = len(next(iter(logs.values())))
time = np.arange(0, T, dt)[:length]

plt.figure()
step_outputs_out = np.array(logs['step.outputs.out']).reshape(length, -1)
for i in range(step_outputs_out.shape[1]):
    plt.step(time, step_outputs_out[:, i], where='post', label='step_outputs_out'+str(i))
sofa_outputs_y = np.array(logs['sofa.outputs.y']).reshape(length, -1)
for i in range(sofa_outputs_y.shape[1]):
    plt.step(time, sofa_outputs_y[:, i], where='post', label='sofa_outputs_y'+str(i))
plt.xlabel('Time [s]')
plt.ylabel('Values')
plt.title('Outputs')
plt.legend()
plt.grid()

plt.figure()
sofa_outputs_markers = np.array(logs['sofa.outputs.markers']).reshape(length, -1)
for i in range(sofa_outputs_markers.shape[1]):
    plt.step(time, sofa_outputs_markers[:, i], where='post', label='sofa_outputs_markers'+str(i))
plt.xlabel('Time [s]')
plt.ylabel('Values')
plt.title('Markers')
plt.legend()
plt.grid()

plt.show()