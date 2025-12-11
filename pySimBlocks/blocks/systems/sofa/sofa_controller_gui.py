from pySimBlocks import Simulator
from pySimBlocks.blocks.systems.sofa import SofaControllerBase
import Sofa

class SofaControllerGui(SofaControllerBase):
    """
    Base class for controller embedding a pySimBlocks model inside the SOFA GUI loop.

    Description:
        SOFA is the time master: at each animation step, this controller
        retrieves measurements from the scene, performs one pySimBlocks
        simulation step, and applies the resulting control inputs back into
        SOFA before the physical integration.

    Required methods:
        - set_inputs(self)
        - get_outputs(self)
        - build_model()  : create self.model, self.sofa_block and variables_to_log

    Optional methods:
        - print_logs()  : print logs at each step (already implemented)
        - save()
    """
    def __init__(self, name="SofaControllerGui"):
        super().__init__(name=name)

        # MUST be filled by child controllers
        self.inputs  = {}
        self.outputs = {}
        self.variables_to_log = []
        self.verbose = False

    # ----------------------------------------------------------------------
    # Abstract interface ---------------------------------------------------
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

    def build_model(self):
        """
        Define the internal pySimBlocks controller model.

        Must create:
            - self.model
            - the exchange block self.sofa_block (SofaExchangeIO)
            - self.variables_to_log
        """
        raise NotImplementedError("build_model() must be implemented by subclass.")


    # ----------------------------------------------------------------------
    # Specific functions ---------------------------------------------------
    # ----------------------------------------------------------------------
    def setup_sim(self, dt):
        """
        Initialize the internal pySimBlocks simulator.

        Parameters
        ----------
        dt : float
            Simulation time step (must match SOFA's dt).
        verbose : bool
            Enable or disable controller logging.
        """
        self.sim = Simulator(self.model, dt=dt, verbose=self.verbose)
        self.sim.initialize()
        self.step_index = 0

    # non mandatory
    def print_logs(self):
        """
        Optional: print selected logged variables at each control step.
        Already implemented
        """
        print(f"\nStep: {self.step_index}")
        for variable in self.variables_to_log:
            print(f"{variable}: {self.sim.logs[variable][-1]}")

    def save(self):
        """
        Optional: save logged data at the end of the simulation.
        To be implented with saving condition.
        """

    # ----------------------------------------------------------------------
    # SOFA event callback ---------------------------------------------------
    # ----------------------------------------------------------------------
    def onAnimateBeginEvent(self, event):
        """
        SOFA callback executed before each physical integration step.

        Sequence:
            1. Read SOFA outputs  → get_outputs()
            2. Push them into the exchange block
            3. Advance pySimBlocks one step → sim.step()
            4. Retrieve controller inputs from exchange block
            5. Apply them to SOFA → set_inputs()
        """
        self.get_outputs()
        for keys, val in self.outputs.items():
            self.sofa_block.outputs[keys] = val

        self.sim.step()
        self.sim._log(self.variables_to_log)

        for key, val in self.sofa_block.inputs.items():
            self.inputs[key] = val
        self.set_inputs()

        if self.verbose:
            self.print_logs()

        self.save()
        self.step_index += 1
