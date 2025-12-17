import numpy as np
from pySimBlocks.core.block import Block


class SofaExchangeIO(Block):
    """
    SOFA exchange interface block.

    Summary:
        Provides an interface between a pySimBlocks model and an external
        SOFA controller by exposing dynamic input and output ports.

    Parameters (overview):
        input_keys : list of str
            Names of externally provided input signals.
        output_keys : list of str
            Names of output signals to be consumed by SOFA.
        scene_file : str
            Path to the SOFA scene file, used only for automatic generation.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            Defined dynamically by input_keys.
        Outputs:
            Defined dynamically by output_keys.

    Notes:
        - This block does not run a SOFA simulation.
        - It acts only as a data exchange interface.
        - The block is stateless.
        - Outputs are produced by the pySimBlocks controller logic.
    """


    direct_feedthrough = False   # necessary: outputs depend immediately on pySimBlocks inputs
    is_source = False

    def __init__(self,
            name: str,
            input_keys: list[str],
            output_keys: list[str],
            scene_file:str="",
            sample_time:float|None = None):
        super().__init__(name, sample_time)

        self.input_keys = input_keys
        self.output_keys = output_keys

        # Declare dynamic ports
        for k in input_keys:
            self.inputs[k] = None
        for k in output_keys:
            self.outputs[k] = None

    def initialize(self, t0: float):
        # Outputs start as zero vectors
        for k in self.output_keys:
            self.outputs[k] = np.zeros((1, 1))

    def output_update(self, t: float, dt: float):
        """
        Outputs are produced by upstream blocks (controller).
        This block itself does nothing but check validity.
        """
        # Ensure inputs exist
        for k in self.input_keys:
            if self.inputs[k] is None:
                raise RuntimeError(f"[{self.name}] Missing input '{k}' at time {t}.")

        # Outputs are set by other blocks (controller chain) through normal propagation.
        pass

    def state_update(self, t: float, dt: float):
        # Stateless block: no internal state
        pass
