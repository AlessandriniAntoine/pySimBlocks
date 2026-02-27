from pathlib import Path

import numpy as np

from pySimBlocks.blocks.systems.sofa import SofaPysimBlocksController

BASE_DIR = Path(__file__).resolve().parent


class FingerController(SofaPysimBlocksController):

    def __init__(self, root, actuator, mo, tip_index=121, name="FingerController"):
        super().__init__(root, name=name)
        self.project_yaml = str((BASE_DIR / "../project.yaml").resolve())

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
        val = self.inputs["cable"]
        if val is None:
            raise ValueError("Input 'cable' is not set")
        val = [val.item()]
        self.actuator.value = val
