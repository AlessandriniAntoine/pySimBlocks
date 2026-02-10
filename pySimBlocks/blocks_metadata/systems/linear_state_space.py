from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class LinearStateSpaceMeta(BlockMeta):

    def __init__(self):
        self.name = "LinearStateSpace"
        self.category = "systems"
        self.type = "linear_state_space"
        self.summary = "Discrete-time linear state-space system."
        self.description = (
            "Implements the discrete-time state-space equations:\n"
            "$$\n"
            "x[k+1] = A x[k] + B u[k]\n"
            "$$\n"
            "$$\n"
            "y[k] = C x[k]\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="A",
                type="matrix",
                required=True,
                autofill=True,
                default=[[0.99]],
                description="State transition matrix."
            ),
            ParameterMeta(
                name="B",
                type="matrix",
                required=True,
                autofill=True,
                default=[[1.0]],
                description="Input matrix."
            ),
            ParameterMeta(
                name="C",
                type="matrix",
                required=True,
                autofill=True,
                default=[[1.0]],
                description="Output matrix."
            ),
            ParameterMeta(
                name="x0",
                type="vector",
                description="Initial state vector."
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
                description="Block execution period."
            )
        ]

        self.inputs = [
            PortMeta(
                name="u",
                display_as="u",
                shape=["m", 1],
                description="Input vector."
            )
        ]

        self.outputs = [
            PortMeta(
                name="x",
                display_as="x",
                shape=["n", 1],
                description="State vector."
            ),
            PortMeta(
                name="y",
                display_as="y",
                shape=["p", 1],
                description="Output vector."
            )
        ]