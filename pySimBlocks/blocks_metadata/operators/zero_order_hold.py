from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class ZeroOrderHoldMeta(BlockMeta):

    def __init__(self):
        self.name = "ZeroOrderHold"
        self.category = "operators"
        self.type = "zero_order_hold"
        self.summary = "Zero-Order Hold (ZOH) block."
        self.description = (
            "Samples the input signal at discrete instants and holds its value\n"
            "constant between sampling instants. The held output is updated when\n"
            "the elapsed time since the last sampling instant reaches the sampling\n"
            "period."
        )

        self.parameters = [
            ParameterMeta(
                name="sample_time",
                type="float",
                required=True
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
                description="Held output signal."
            )
        ]