import numpy as np

from pySimBlocks.blocks.systems.sofa import SofaPysimBlocksController


class FingerController(SofaPysimBlocksController):
    """Exchange signals between the finger scene and the pySimBlocks diagram.

    Input:
        cable: displacement command applied to the cable actuator, shape (1, 1).

    Outputs:
        tip: 3D position of the fingertip, shape (3, 1).
        measure: vertical (y) position of the fingertip, shape (1, 1).
    """

    def __init__(self, actuator, mo, tip_index=121, project_yaml=None,
                 name="FingerController"):
        # project_yaml is provided by the scene (--project-yaml argument).
        super().__init__(project_yaml=project_yaml, name=name)

        self.mo = mo
        self.actuator = actuator
        self.tip_index = tip_index
        self.verbose = False  # Set to True to print debug information at each step

        # Signals exchanged with pySimBlocks. The keys declared in the
        # SofaPlant block (input_keys / output_keys) must be a subset of these.
        self.inputs = {"cable": None}
        self.outputs = {"tip": None, "measure": None}

    def get_outputs(self):
        # Outputs must be column vectors, with the same shape at every call.
        tip = self.mo.position[self.tip_index].copy()
        self.outputs["tip"] = np.asarray(tip).reshape(-1, 1)
        self.outputs["measure"] = np.asarray(tip[1]).reshape(-1, 1)

    def set_inputs(self):
        val = self.inputs["cable"]
        if val is None:
            raise ValueError("Input 'cable' is not set")
        self.actuator.value = [val.item()]
