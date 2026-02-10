from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class GainMeta(BlockMeta):

    def __init__(self):
        self.name = "Gain"
        self.category = "operators"
        self.type = "gain"
        self.summary = "Static linear gain block."
        self.description = (
            "Computes:\n"
            "$$\n"
            "y = K \\cdot u\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="gain",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=1.0,
                description="Gain coefficient."
            ),
            ParameterMeta(
                name="multiplication",
                type="enum",
                autofill=True,
                default="Element wise (K * u)",
                enum=["Element wise (K * u)", "Matrix (K @ u)", "Matrix (u @ K)"],
                description="Type of multiplication operation."
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
                shape=["m", "m"],
                description="Output signal."
            )
        ]