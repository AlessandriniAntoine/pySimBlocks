import Sofa

class SofaControllerBase(Sofa.Core.Controller):
    """
    Base class for controllers used with pySimBlocks SofaPlant/SofaIO blocks.

    Responsibilities:
        - define input dictionary
        - define output dictionary
        - implement set_inputs()
        - implement get_outputs()
        - automatic integration with SOFA simulation loop

    Required methods:
        - set_inputs(self)
        - get_outputs(self)
    """

    def __init__(self, name="SofaControllerBase"):
        super().__init__(name=name)

        # MUST be filled by child controllers
        self.inputs  = {}
        self.outputs = {}

    # ----------------------------------------------------------------------
    # Abstract interface ----------------------------------------------------
    # ----------------------------------------------------------------------
    def set_inputs(self):
        """
        Apply inputs from pySimBlocks to SOFA components.
        Must be implemented by child classes.
        """
        raise NotImplementedError("set_inputs() must be implemented by subclass.")

    def get_outputs(self):
        """
        Read state from SOFA components and populate self.outputs.
        Must be implemented by child classes.
        """
        raise NotImplementedError("get_outputs() must be implemented by subclass.")

    # ----------------------------------------------------------------------
    # SOFA event callback ---------------------------------------------------
    # ----------------------------------------------------------------------
    def onAnimateBeginEvent(self, event):
        """
        SOFA callback executed at each simulation step.
        We first read outputs (SOFA → pySimBlocks),
        then apply new inputs (pySimBlocks → SOFA).
        """
        self.get_outputs()
        self.set_inputs()
