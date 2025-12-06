import numpy as np
# Auto imports
from pySimBlocks.blocks.operators import DiscreteIntegrator
from pySimBlocks.blocks.operators import Gain
from pySimBlocks.blocks.operators import Sum
from pySimBlocks.blocks.sources import Constant
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import SofaSystem
from pySimBlocks import Model, Simulator
from parameters_auto import *

model = Model('auto_model')

step = Step('step', value_before=step_value_before, value_after=step_value_after, t_step=step_t_step)
model.add_block(step)

error = Sum('error', num_inputs=error_num_inputs, signs=error_signs)
model.add_block(error)

Kp = Gain('Kp', gain=Kp_gain)
model.add_block(Kp)

Ki = Gain('Ki', gain=Ki_gain)
model.add_block(Ki)

discrete_integrator = DiscreteIntegrator('discrete_integrator', initial_state=discrete_integrator_initial_state)
model.add_block(discrete_integrator)

sum = Sum('sum', num_inputs=sum_num_inputs)
model.add_block(sum)

sofa = SofaSystem('sofa', scene_file=sofa_scene_file, input_keys=sofa_input_keys, output_keys=sofa_output_keys)
model.add_block(sofa)

sofa_ol = SofaSystem('sofa_ol', scene_file=sofa_ol_scene_file, input_keys=sofa_ol_input_keys, output_keys=sofa_ol_output_keys)
model.add_block(sofa_ol)

constant = Constant('constant', value=constant_value)
model.add_block(constant)

model.connect('step', 'out', 'error', 'in1')
model.connect('error', 'out', 'Kp', 'in')
model.connect('error', 'out', 'discrete_integrator', 'in')
model.connect('Kp', 'out', 'sum', 'in1')
model.connect('discrete_integrator', 'out', 'Ki', 'in')
model.connect('Ki', 'out', 'sum', 'in2')
model.connect('sum', 'out', 'sofa', 'cable')
model.connect('sofa', 'measure', 'error', 'in2')
model.connect('constant', 'out', 'sofa_ol', 'cable')

sim = Simulator(model, dt=dt)