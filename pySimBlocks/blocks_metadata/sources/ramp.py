from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class RampMeta(BlockMeta):

    def __init__(self):
        self.name = "Ramp"
        self.category = "sources"
        self.type = "ramp"
        self.summary = "Multi-dimensional ramp signal source."
        self.description = (
            "Generates a ramp signal defined by:\n"
            "$$\n"
            "y_i(t) = o_i + s_i \\max(0, t - t_{0,i})\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="slope",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=[[1.0]],
                description="Ramp slope for each output dimension."
            ),
            ParameterMeta(
                name="start_time",
                type="scalar | vector | matrix",
                description="Time at which the ramp starts."
            ),
            ParameterMeta(
                name="offset",
                type="scalar | vector | matrix",
                description="Output value before the ramp starts."
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
                description="Block execution period."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"],
                description="Ramp output signal."
            )
        ]