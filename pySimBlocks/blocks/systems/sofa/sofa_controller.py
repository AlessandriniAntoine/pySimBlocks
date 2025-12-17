from pathlib import Path
import Sofa
from pySimBlocks import Model, Simulator
from pySimBlocks.project.load_simulation_config import load_simulation_config
from pySimBlocks.project.build_model import adapt_model_for_sofa, build_model_from_dict


class SofaPysimBlocksController(Sofa.Core.Controller):
    """
    Base class for controller to enable Sofa Simulation Loop and pySimBlocks to interact.

    Description:
        - SOFA_MASTER: SOFA is the time master.
            model_yaml + parameters_yaml required
            pysimblocks time step must be a multiple of sofa time step.
            At each pysimblocks step, the controller:
                1) reads measurements from the scene
                2) performs one pySimBlocks step
                3) applies the computed control inputs

        - Non-SOFA_MASTER: pySimBlocks is the time master.
                            The controller is used ONLY as an I/O shell.
                            No pySimBlocks model is built or executed.

    Required methods:
        - set_inputs(self)
        - get_outputs(self)

    Optional methods:
        - build_model()  : create self.model, self.sofa_block and variables_to_log
        - print_logs()  : print logs at each step (already implemented)
        - save()

    optional parameter:
        - variables_to_log: list of signal to log
    """

    def __init__(self, name="SofaControllerGui"):
        super().__init__(name=name)

        self.IS_READY = False
        self.SOFA_MASTER = True

        # MUST be filled by child controllers
        self.inputs  = {}
        self.outputs = {}
        self.variables_to_log = []
        self.verbose = False

        self.dt = None
        self.sim = None
        self.step_index = 0

        self.model_yaml= None
        self.parameters_yaml = None

    # ----------------------------------------------------------------------
    # Common             ---------------------------------------------------
    # ----------------------------------------------------------------------
    def prepare_scene(self):
        """
        Optional initialization hook executed before pySimBlocks starts.

        Purpose:
            - wait for any preparation condition (fixed number of steps,
            convergence, stabilization, etc.),
            - optionally record initial measurements or offsets.

        The user must set `self.IS_READY = True` when the scene is ready to start
        the pySimBlocks control loop.
        """
        self.IS_READY = True

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
    # Optionnal methods. --------------
    # ----------------------------------------------------------------------
    def save(self):
        """
        Optional: executed at each control step.
        Override this method to save logs or export custom data.
        The default implementation does nothing.
        """
        pass

    # ----------------------------------------------------------------------
    # SOFA event callback --------------------------------------------------
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
        if self.SOFA_MASTER:
            if self.sim is None:
                self._prepare_pysimblocks()

            if not self.IS_READY:
                self.prepare_scene()

            if self.IS_READY:
                if self.counter % self.ratio ==0:
                    self.get_outputs()
                    for keys, val in self.outputs.items():
                        self._sofa_block.outputs[keys] = val

                    self.sim.step()
                    self.sim._log(self.sim_cfg.logging)

                    for key, val in self._sofa_block.inputs.items():
                        self.inputs[key] = val
                    self.set_inputs()

                    if self.verbose:
                        self._print_logs()

                    self.save()
                    self.sim_index += 1
                    self.counter = 0
                self.counter += 1

        self.step_index += 1

    # ----------------------------------------------------------------------
    # Internal methods -----------------------------------------------------
    # ----------------------------------------------------------------------
    def _build_model(self):
        """
        Define the internal pySimBlocks controller model.
        Mandatory if purpose to be used in Sofa Simulation (SOFA_MASTER)

        Must create:
            - self.model
            - the exchange block self.sofa_block (SofaExchangeIO)
            - self.variables_to_log
        """
        if self.parameters_yaml is not None:
            self.sim_cfg, self.model_cfg = load_simulation_config(self.parameters_yaml)
        if self.model_yaml is not None:
            model_dict = adapt_model_for_sofa(Path(self.model_yaml))
            self.model = Model("sofa_model")
            build_model_from_dict(self.model, model_dict, self.model_cfg)


    def _prepare_pysimblocks(self):
        """
        Called once SOFA is initialized AND if SOFA is the master.
        Initialize the pysimblock struture.
        """
        if self.SOFA_MASTER and (self.model_yaml is None or self.parameters_yaml is None):
            raise RuntimeError("SOFA_MASTER=True requires model_yaml and parameters_yaml.")
        if self.dt is None:
            raise ValueError("Sample time dt Must be set at initialization.")

        self._build_model()
        self._detect_sofa_exchange_block()
        self.sim = Simulator(self.model, self.sim_cfg, verbose=self.verbose)
        self.sim.initialize()
        self.sim_index = 0

        ratio = self.sim_cfg.dt / self.dt
        if abs(ratio - round(ratio)) > 1e-12:
            raise ValueError(
                            f"pySimBlocks sample time={self.sim_cfg.dt} "
                            f"is not a multiple of Sofa sample time={self.dt}."
                        )
        self.ratio = int(round(ratio))
        self.counter = 0


    def _print_logs(self):
        """
        Optional: print selected logged variables at each control step.
        Already implemented
        """
        print(f"\nStep: {self.sim_index}")
        for variable in self.sim_cfg.logging:
            print(f"{variable}: {self.sim.logs[variable][-1]}")


    def _detect_sofa_exchange_block(self):
        """
        Detect the SofaExchangeIO block inside self.model.
        Must be called after build_model().
        """
        from pySimBlocks.blocks.systems.sofa.sofa_exchange_i_o import SofaExchangeIO

        candidates = [blk for blk in self.model.blocks.values() if isinstance(blk, SofaExchangeIO)]

        if len(candidates) == 0:
            raise RuntimeError(
                "No SofaExchangeIO block found in the model. "
                "The controller must include exactly one SOFA exchange block."
            )

        if len(candidates) > 1:
            raise RuntimeError(
                f"Multiple SofaExchangeIO blocks found ({len(candidates)}). "
                "Only one SOFA IO block is allowed."
            )

        self._sofa_block = candidates[0]
