from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class DelayMeta(BlockMeta):

    def __init__(self):
        self.name = "Delay"
        self.category = "operators"
        self.type = "delay"
        self.summary = "N-step discrete-time delay block."
        self.description = (
            "Implements a discrete delay of $N$ simulation steps:\n"
            "$$\n"
            "y[k] = u[k - N]\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="num_delays",
                type="int",
                autofill=True,
                default=1
            ),
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
            ),
            PortMeta(
                name="reset",
                display_as="reset",
                shape=[],
                description="Reset signal (0/1). When high (1), the delay state is reset to the initial output value."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"],
                description="Delayed output signal."
            )
        ]