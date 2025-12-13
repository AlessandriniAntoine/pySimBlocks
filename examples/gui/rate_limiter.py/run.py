import numpy as np
import matplotlib.pyplot as plt
from model import simulator, T, dt

logs = simulator.run(T=T, variables_to_log=[
    'ramp.outputs.out',
    'rate_limiter.outputs.out',
    'dead_zone.outputs.out',
    'sinusoidal.outputs.out',
])
print('Simulation complete.')

length = len(next(iter(logs.values())))
time = np.array(logs['time'])

plt.figure()
ramp_outputs_out = np.array(logs['ramp.outputs.out']).reshape(length, -1)
for i in range(ramp_outputs_out.shape[1]):
    plt.step(time, ramp_outputs_out[:, i], where='post', label='ramp_outputs_out'+str(i))
rate_limiter_outputs_out = np.array(logs['rate_limiter.outputs.out']).reshape(length, -1)
for i in range(rate_limiter_outputs_out.shape[1]):
    plt.step(time, rate_limiter_outputs_out[:, i], where='post', label='rate_limiter_outputs_out'+str(i))
plt.xlabel('Time [s]')
plt.ylabel('Values')
plt.title('Rate')
plt.legend()
plt.grid()

plt.figure()
sinusoidal_outputs_out = np.array(logs['sinusoidal.outputs.out']).reshape(length, -1)
for i in range(sinusoidal_outputs_out.shape[1]):
    plt.step(time, sinusoidal_outputs_out[:, i], where='post', label='sinusoidal_outputs_out'+str(i))
dead_zone_outputs_out = np.array(logs['dead_zone.outputs.out']).reshape(length, -1)
for i in range(dead_zone_outputs_out.shape[1]):
    plt.step(time, dead_zone_outputs_out[:, i], where='post', label='dead_zone_outputs_out'+str(i))
plt.xlabel('Time [s]')
plt.ylabel('Values')
plt.title('Dead Zone')
plt.legend()
plt.grid()

plt.show()