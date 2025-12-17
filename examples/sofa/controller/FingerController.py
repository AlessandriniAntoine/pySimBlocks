import numpy as np
import Sofa

from pySimBlocks.blocks.systems.sofa import SofaPysimBlocksController

class FingerController(SofaPysimBlocksController):

    def __init__(self, root, actuator, mo, tip_index=121, verbose=True, name="FingerController"):
        super().__init__(name=name)

        self.parameters_yaml = "parameters.yaml"
        self.model_yaml = "model.yaml"

        self.mo = mo
        self.actuator = actuator
        self.tip_index = tip_index
        self.verbose = verbose
        self.dt = root.dt.value

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
