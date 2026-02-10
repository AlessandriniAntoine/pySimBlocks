from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class DiscreteDerivatorMeta(BlockMeta):

    def __init__(self):
        self.name = "DiscreteDerivator"
        self.category = "operators"
        self.type = "discrete_derivator"
        self.summary = "Discrete-time differentiator block."
        self.description = (
            "Computes a backward finite-difference approximation of the derivative:\n"
            "$$\n"
            "y[k] = \\frac{u[k] - u[k-1]}{dt}\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="initial_output",
                type="scalar | vector | matrix"
            ),
            ParameterMeta(
                name="sample_time",
                type="float"
            )
        ]

        self.inputs = [
            PortMeta(
                name="in",
                display_as="in",
                shape=["n", "m"],
                description="Input signal."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"],
                description="Discrete-time derivative of the input."
            )
        ]