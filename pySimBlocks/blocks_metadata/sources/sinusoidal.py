from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class SinusoidalMeta(BlockMeta):

    def __init__(self):
        self.name = "Sinusoidal"
        self.category = "sources"
        self.type = "sinusoidal"
        self.summary = "Multi-dimensional sinusoidal signal source."
        self.description = (
            "Generates a sinusoidal signal defined by:\n"
            "$$\n"
            "y_i(t) = A_i \\sin(2\\pi f_i t + \\varphi_i) + o_i\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="amplitude",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=[[1.0]],
                description="Sinusoidal amplitude."
            ),
            ParameterMeta(
                name="frequency",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=[[1.0]],
                description="Sinusoidal frequency in Hertz."
            ),
            ParameterMeta(
                name="phase",
                type="scalar | vector | matrix",
                description="Phase shift in radians."
            ),
            ParameterMeta(
                name="offset",
                type="scalar | vector | matrix",
                description="Constant offset added to the signal."
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
                description="Sinusoidal output signal."
            )
        ]