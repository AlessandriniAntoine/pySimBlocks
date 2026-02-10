from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class SaturationMeta(BlockMeta):

    def __init__(self):
        self.name = "Saturation"
        self.category = "operators"
        self.type = "saturation"
        self.summary = "Discrete-time saturation operator."
        self.description = (
            "Applies element-wise saturation to the input signal:\n"
            "$$\n"
            "y[k] = \\mathrm{clip}(u[k], u_{\\min}, u_{\\max})\n"
            "$$\n"
            "where $u_{\\min}$ and $u_{\\max}$ define the lower and upper bounds."
        )

        self.parameters = [
            ParameterMeta(
                name="u_min",
                type="scalar | vector | matrix"
            ),
            ParameterMeta(
                name="u_max",
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
                shape=["n", 1],
                description="Input signal."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"],
                description="Saturated output signal."
            )
        ]