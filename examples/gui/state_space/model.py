import numpy as np
# Auto imports
from pySimBlocks.blocks.operators import Delay
from pySimBlocks.blocks.operators import Gain
from pySimBlocks.blocks.operators import Sum
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import LinearStateSpace
from pySimBlocks import Model, Simulator
from parameters_auto import *

model = Model('auto_model')

A = Gain('A', gain=A_gain)
model.add_block(A)

B = Gain('B', gain=B_gain)
model.add_block(B)

C = Gain('C', gain=C_gain)
model.add_block(C)

delay = Delay('delay', num_delays=delay_num_delays, initial_output=delay_initial_output)
model.add_block(delay)

sum = Sum('sum', num_inputs=sum_num_inputs, signs=sum_signs)
model.add_block(sum)

step = Step('step', value_before=step_value_before, value_after=step_value_after, t_step=step_t_step)
model.add_block(step)

plant = LinearStateSpace('plant', A=plant_A, B=plant_B, C=plant_C, x0=plant_x0)
model.add_block(plant)

model.connect('A', 'out', 'sum', 'in2')
model.connect('B', 'out', 'sum', 'in1')
model.connect('sum', 'out', 'delay', 'in')
model.connect('delay', 'out', 'A', 'in')
model.connect('delay', 'out', 'C', 'in')
model.connect('step', 'out', 'B', 'in')
model.connect('step', 'out', 'plant', 'u')

sim = Simulator(model, dt=dt)