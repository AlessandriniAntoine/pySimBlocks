import numpy as np
import Sofa

from pySimBlocks import Model
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.operators import Sum
from pySimBlocks.blocks.controllers import Pid
from pySimBlocks.blocks.systems.sofa import SofaExchangeIO, SofaPysimBlocksController


class FingerController(SofaPysimBlocksController):

    def __init__(self, root, actuator, mo, tip_index=121, verbose=True, name="FingerController"):
        super().__init__(name=name)

        self.mo = mo
        self.actuator = actuator
        self.tip_index = tip_index
        self.verbose = verbose
        self.dt = root.dt.value

        # Inputs & outputs dictionaries A METTRE AVANT SETUP_SIM
        self.inputs = { "cable": None }
        self.outputs = { "tip": None, "measure": None }

        self.last_tip = 0

    # ========================================================
    # Commun functions
    # ========================================================

    def prepare_scene(self):
        current_tip = self.mo.position[self.tip_index].copy()
        if np.linalg.norm(current_tip - self.last_tip) < 1e-2:
            self.initial_tip = current_tip
            self.IS_READY = True
        self.last_tip = current_tip

    def get_outputs(self):
        tip = self.mo.position[self.tip_index].copy() - self.initial_tip
        self.outputs["tip"] = np.asarray(tip).reshape(-1, 1)
        self.outputs["measure"] = np.asarray(tip[1]).reshape(-1, 1)

    def set_inputs(self):
        # 1. READ INPUT -------------------------------------
        val = self.inputs["cable"]

        # Safe default for first initialization call
        if val is None:
            # ↓↓↓ Valeur par défaut pour l’initialisation
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


    def save(self):
        if np.isclose(self.sim.logs["time"][-1], 5.):
            logs = self.sim.logs
            length = len(logs["time"])
            np.savez("data_gui.npz",
                time=np.array(self.sim.logs["time"]).reshape(length, -1),
                reference=np.array(self.sim.logs["step.outputs.out"]).reshape(length, -1),
                command=np.array(self.sim.logs["pid.outputs.u"]).reshape(length, -1),
                measure=np.array(self.sim.logs["sofa_io.outputs.measure"]).reshape(length, -1)
        )

    # ========================================================
    # specific functions
    # ========================================================
    def build_model(self):
        # pysimblock controller:
        self.step = Step(name="step", value_before=[[0.0]], value_after=[[8.0]], start_time=0.4)
        self.error = Sum(name="error", num_inputs=2, signs=[1, -1])
        self.pid = Pid("pid", Kp=0.3, Ki=0.8, controller="PI")

        self.sofa_block = SofaExchangeIO(name="sofa_io", input_keys=["cable"], output_keys=["measure"])

        # --- Build the model ---
        self.model = Model(name="sofa_finger_controller")
        for block in [self.step, self.error, self.pid, self.sofa_block]:
            self.model.add_block(block)

        self.model.connect("step", "out", "error", "in1")
        self.model.connect("sofa_io", "measure", "error", "in2")
        self.model.connect("error", "out", "pid", "e")
        self.model.connect("pid", "u", "sofa_io", "cable")

        self.variables_to_log = ["step.outputs.out", "pid.outputs.u", "sofa_io.outputs.measure"]
