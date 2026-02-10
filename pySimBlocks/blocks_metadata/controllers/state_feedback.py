from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class StateFeedBackMeta(BlockMeta):
    def __init__(self):
        self.name = "StateFeedback"
        self.category = "controllers"
        self.type = "state_feedback"
        self.summary = "Discrete-time state-feedback controller."
        self.description = (
            "Implements the static control law:\n"
            "$$\n"
            "u[k] = G r[k] - K x[k]\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="K",
                type="matrix",
                required=True,
                description="State feedback gain matrix."
            ),
            ParameterMeta(
                name="G",
                type="matrix",
                required=True,
                description="Reference feedforward gain matrix."
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
                description="Block execution period."
            ),
        ]

        self.inputs = [
            PortMeta(
                name="r",
                display_as="r",
                shape=["p", 1]
            ),
            PortMeta(
                name="x",
                display_as="x",
                shape=["n", 1],
                description="State measurement vector."
            )
        ]

        self.outputs = [
            PortMeta(
                name="u",
                display_as="u",
                shape=["m", 1],
                description="Control input vector."
            ),
        ]