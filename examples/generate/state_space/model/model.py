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

ref = Step('ref', value_before=ref_value_before, value_after=ref_value_after, t_step=ref_t_step)
model.add_block(ref)

B = Gain('B', gain=B_gain)
model.add_block(B)

sum = Sum('sum', signs=sum_signs)
model.add_block(sum)

delay = Delay('delay', initial_output=delay_initial_output)
model.add_block(delay)

A = Gain('A', gain=A_gain)
model.add_block(A)

plant = LinearStateSpace('plant', A=plant_A, B=plant_B, C=plant_C, x0=plant_x0)
model.add_block(plant)

model.connect('ref', 'out', 'B', 'in')
model.connect('B', 'out', 'sum', 'in1')
model.connect('A', 'out', 'sum', 'in2')
model.connect('sum', 'out', 'delay', 'in')
model.connect('delay', 'out', 'A', 'in')
model.connect('ref', 'out', 'plant', 'u')

sim = Simulator(model, dt=dt)