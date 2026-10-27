import numpy as np

from pySimBlocks.blocks.systems.sofa import SofaPysimBlocksController


class FingerController(SofaPysimBlocksController):

    def __init__(self, actuator, mo, tip_index=121, project_yaml="",
                 name="FingerController"):
        super().__init__(project_yaml=project_yaml, name=name)

        self.mo = mo
        self.actuator = actuator
        self.tip_index = tip_index
        self.verbose = False # Set to True to print debug information at each step

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
        self.actuator.value = [val.item()]
