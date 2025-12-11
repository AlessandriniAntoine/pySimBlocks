import numpy as np
from pySimBlocks.core.block import Block

class SofaExchangeIO(Block):
    """
    Interface block for embedding a pySimBlocks model inside a SOFA controller.

    Description:
        This block does NOT run a SOFA simulation. It only exposes:
            - input ports written by an external SOFA controller
            - output ports produced by the pySimBlocks model

        It is fully stateless and acts only as a data bridge.
        Unlike SofaPlant (full SOFA simulation), this block *does not runs* the SOFA simulation itself but should be set in a SOFA controller.

    Parameters:
        name: str
            Block name.
        input_keys: list of str
            Names of externally provided input signals.
        output_keys: list of str
            Names of output signals to be consumed by SOFA.

    Inputs:
        Dynamic — specified by input_keys.

    Outputs:
        Dynamic — specified by output_keys.
    """

    direct_feedthrough = False   # necessary: outputs depend immediately on pySimBlocks inputs
    is_source = False

    def __init__(self, name: str, input_keys: list[str], output_keys: list[str]):
        super().__init__(name)

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

    def output_update(self, t: float):
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
