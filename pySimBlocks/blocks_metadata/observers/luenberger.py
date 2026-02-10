from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class LuenbergerMeta(BlockMeta):

    def __init__(self):
        self.name = "Luenberger"
        self.category = "observers"
        self.type = "luenberger"
        self.summary = "Discrete-time Luenberger state observer."
        self.description = (
            "Implements the discrete-time observer equations:\n"
            "$$\n"
            "x̂[k+1] = A x̂[k] + B u[k] + L (y[k] - C x̂[k])\n"
            "$$\n"
            "$$\n"
            "ŷ[k] = C x̂[k]\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="A",
                type="matrix",
                required=True,
                description="System state matrix."
            ),
            ParameterMeta(
                name="B",
                type="matrix",
                required=True,
                description="Input matrix."
            ),
            ParameterMeta(
                name="C",
                type="matrix",
                required=True,
                description="Output matrix."
            ),
            ParameterMeta(
                name="L",
                type="matrix",
                required=True,
                description="Observer gain matrix."
            ),
            ParameterMeta(
                name="x0",
                type="vector",
                description="Initial estimated state."
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
                description="Block execution period."
            ),
        ]

        self.inputs = [
            PortMeta(
                name="in",
                display_as="u",
                shape=["m", 1],
                description="Control input."
            ),
            PortMeta(
                name="measurement",
                display_as="y",
                shape=["p", 1],
                description="Measured output."
            ),
        ]

        self.outputs = [
            PortMeta(
                name="state_estimate",
                display_as="x_hat",
                shape=["n", 1],
                description="Estimated state vector."
            ),
            PortMeta(
                name="output_estimate",
                display_as="y_hat",
                shape=["p", 1],
                description="Estimated output."
            ),
        ]