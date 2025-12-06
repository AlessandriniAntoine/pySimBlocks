import numpy as np
# Auto imports
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import SofaSystem
from pySimBlocks import Model, Simulator
from parameters_auto import *

model = Model('auto_model')

step = Step('step', value_before=step_value_before, value_after=step_value_after, t_step=step_t_step)
model.add_block(step)

sofa = SofaSystem('sofa', scene_file=sofa_scene_file, input_keys=sofa_input_keys, output_keys=sofa_output_keys)
model.add_block(sofa)

model.connect('step', 'out', 'sofa', 'u')

sim = Simulator(model, dt=dt)