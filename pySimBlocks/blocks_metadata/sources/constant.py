from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class ConstantMeta(BlockMeta):
    
    def __init__(self):
        self.name = "Constant"
        self.category = "sources"
        self.type = "constant"
        self.summary = "Constant signal source."
        self.description = (
            "Generates a constant output signal:\n"
            "$$\n"
            "y(t) = c"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name = "value", 
                type = "scalar | vector | matrix",
                required = True,
                autofill = True,
                default = [[1.0]],
                description = "Constant output value."
            ),

            ParameterMeta(
                name = "sample_time",
                type = "float",
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"],
                description="Constant output signal."
            )
        ]