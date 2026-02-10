from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class DeadZoneMeta(BlockMeta):

    def __init__(self):
        self.name = "DeadZone"
        self.category = "operators"
        self.type = "dead_zone"
        self.summary = "Discrete-time dead zone operator."
        self.description = (
            "Applies a dead-zone nonlinearity to the input signal:\n"
            "$$\n"
            "y = 0 \\quad \\text{if } \\text{lower\\_bound} \\le u \\le \\text{upper\\_bound}\n"
            "$$\n"
            "$$\n"
            "y = u - \\text{upper\\_bound} \\quad \\text{if } u > \\text{upper\\_bound}\n"
            "$$\n"
            "$$\n"
            "y = u - \\text{lower\\_bound} \\quad \\text{if } u < \\text{lower\\_bound}\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="lower_bound",
                type="scalar | vector | matrix",
                default=0.0
            ),
            ParameterMeta(
                name="upper_bound",
                type="scalar | vector | matrix",
                default=0.0
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
                description="Output signal after dead-zone operation."
            )
        ]