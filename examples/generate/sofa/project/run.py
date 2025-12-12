import numpy as np
import matplotlib.pyplot as plt
from model import simulator, T, dt

logs = simulator.run(T=T, variables_to_log=[
    'step.outputs.out',
    'sofa.outputs.measure',
    'pid.outputs.u',
])
print('Simulation complete.')

length = len(next(iter(logs.values())))
time = np.array(logs['time'])

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
pid_outputs_u = np.array(logs['pid.outputs.u']).reshape(length, -1)
for i in range(pid_outputs_u.shape[1]):
    plt.step(time, pid_outputs_u[:, i], where='post', label='pid_outputs_u'+str(i))
plt.xlabel('Time [s]')
plt.ylabel('Values')
plt.title('Command')
plt.legend()
plt.grid()

plt.show()