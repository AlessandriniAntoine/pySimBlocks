import numpy as np
from pySimBlocks.blocks.systems.sofa import SofaPysimBlocksController

import Sofa

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent




class FingerController(SofaPysimBlocksController):

    def __init__(self, root, actuator, mo, tip_index=121, name="FingerController"):
        super().__init__(name=name)
        self.parameters_yaml = str((BASE_DIR / "../parameters.yaml").resolve())
        self.model_yaml = str((BASE_DIR / "../model.yaml").resolve())

        self.mo = mo
        self.actuator = actuator
        self.tip_index = tip_index
        self.dt = root.dt.value
        self.verbose = True

        # Inputs & outputs dictionaries
        self.inputs = { "cable": None }
        self.outputs = { "tip": None, "measure": None }


    def get_outputs(self):
        tip = self.mo.position[self.tip_index].copy()
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
