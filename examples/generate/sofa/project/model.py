from parameters_auto import *
from pySimBlocks import Model, Simulator
from pySimBlocks.blocks.controllers.pid import Pid
from pySimBlocks.blocks.operators.sum import Sum
from pySimBlocks.blocks.sources.step import Step
from pySimBlocks.blocks.systems.sofa.sofa_plant import SofaPlant

model = Model('auto_model')

step = Step('step', value_before=step_value_before, value_after=step_value_after, start_time=step_start_time)
model.add_block(step)

error = Sum('error', num_inputs=error_num_inputs, signs=error_signs)
model.add_block(error)

pid = Pid('pid', controller=pid_controller, Kp=pid_Kp, Ki=pid_Ki)
model.add_block(pid)

sofa = SofaPlant('sofa', scene_file=sofa_scene_file, input_keys=sofa_input_keys, output_keys=sofa_output_keys)
model.add_block(sofa)

model.connect('step', 'out', 'error', 'in1')
model.connect('error', 'out', 'pid', 'e')
model.connect('pid', 'u', 'sofa', 'cable')
model.connect('sofa', 'measure', 'error', 'in2')

simulator = Simulator(model, dt=dt)