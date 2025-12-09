import numpy as np
from pySimBlocks.blocks.sources import Step
from pySimBlocks import Model, Simulator

for t_step in [.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1., 1.1]:
# for t_step in [0.8]:
    model = Model('auto_model')
    step = Step('step', value_before=0., value_after=1., start_time=t_step)
    model.add_block(step)
    sim = Simulator(model, dt=0.1)

    logs = sim.run(T=2.5, variables_to_log=[
        'step.outputs.out',
    ])
    print("------------------------------------------")
    print('Simulation complete. for t_step: ', t_step)

    length = len(next(iter(logs.values())))
    time = np.array(logs['time'])
    out = np.array(logs['step.outputs.out']).reshape(length, -1)

    for t, o in zip(time, out):
        print(f"Time: {t}, out: {o}")
