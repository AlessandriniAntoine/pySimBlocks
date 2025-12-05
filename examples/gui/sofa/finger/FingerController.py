import numpy as np
import Sofa


class FingerController(Sofa.Core.Controller):

    def __init__(self, actuator, mo, tip_index=121, name="FingerController"):
        super().__init__(name=name)

        self.mo = mo
        self.actuator = actuator
        self.tip_index = tip_index

        # Inputs & outputs dictionaries
        self.inputs = { "cable": None }
        self.outputs = { "tip": None, "measure": None }


    def onAnimateBeginEvent(self, event):

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

        # 2. COMPUTE OUTPUT ---------------------------------
        tip = self.mo.position[self.tip_index].copy()
        self.outputs["tip"] = np.asarray(tip).reshape(-1, 1)
        self.outputs["measure"] = np.asarray(tip[1]).reshape(-1, 1)  # Y coordinate as measurement
