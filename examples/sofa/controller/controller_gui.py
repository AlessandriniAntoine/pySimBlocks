import numpy as np
import Sofa

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks.systems import SofaIO
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.operators import Sum
from pySimBlocks.blocks.controllers import Pid


class FingerController(Sofa.Core.Controller):

    def __init__(self, root, actuator, mo, tip_index=121, name="FingerController"):
        super().__init__(name=name)

        self.root = root
        self.actuator = actuator
        self.mo = mo
        self.tip_index = tip_index

        # --- Create the simulator ---
        self.build_model()
        self.sim = Simulator(self.model, dt=self.root.dt.value)
        self.sim.initialize()

        # Inputs & outputs dictionaries
        self.inputs = { "cable": None }
        self.outputs = { "measure": None }


        self.step_index = 0


    def build_model(self):
        # pysimblock controller:
        self.step = Step(name="step", value_before=[[0.0]], value_after=[[8.0]], start_time=0.4)
        self.error = Sum(name="error", num_inputs=2, signs=[1, -1])
        self.pid = Pid("pid", Kp=0.3, Ki=0.8, Kd=0.000)

        self.sofa_block = SofaIO(name="sofa_io", input_keys=["cable"], output_keys=["measure"])

        # --- Build the model ---
        self.model = Model(name="sofa_finger_controller")
        for block in [self.step, self.error, self.pid, self.sofa_block]:
            self.model.add_block(block)

        self.model.connect("step", "out", "error", "in1")
        self.model.connect("sofa_io", "measure", "error", "in2")
        self.model.connect("error", "out", "pid", "e")
        self.model.connect("pid", "u", "sofa_io", "cable")

        self.variables_to_log = ["step.outputs.out", "pid.outputs.u", "sofa_io.outputs.measure"]

    def update_output(self):
        # TO BE COMPLETED BY THE USER
        tip = self.mo.position[self.tip_index].copy()
        y = np.asarray(tip[1].reshape(-1, 1))
        self.outputs["measure"] = y

    def set_inputs(self):
        # TO BE COMPLETED BY THE USER
        val = self.inputs["cable"]
        if val is None:
            val = 0.0

        # Convert input to Sofa format
        if isinstance(val, np.ndarray):
            processed = val.flatten().tolist()
        elif isinstance(val, (list, tuple)):
            processed = val
        else:
            processed = [float(val)]

        # Apply to actuator
        self.actuator.value = processed

    def print_logs(self):
        print(f"\nStep: {self.step_index}")
        for variable in self.variables_to_log:
            print(f"{variable}: {self.sim.logs[variable][-1]}")


    def onAnimateBeginEvent(self, event):
        # update output of SOFA
        self.update_output()
        for keys, val in self.outputs.items():
            self.sofa_block.outputs[keys] = val

    def onAnimateEndEvent(self, event):
        self.sim.step()
        self.sim._log(self.variables_to_log)

        for key, val in self.sofa_block.inputs.items():
            self.inputs[key] = val

        self.set_inputs()
        self.print_logs()


        if np.isclose(self.sim.logs["time"][-1], 5.):
            logs = self.sim.logs
            length = len(logs["time"])
            np.savez("data_gui.npz",
                time=np.array(self.sim.logs["time"]).reshape(length, -1),
                reference=np.array(self.sim.logs["step.outputs.out"]).reshape(length, -1),
                command=np.array(self.sim.logs["pid.outputs.u"]).reshape(length, -1),
                measure=np.array(self.sim.logs["sofa_io.outputs.measure"]).reshape(length, -1)
        )

        self.step_index += 1
