from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class WhiteNoiseMeta(BlockMeta):

    def __init__(self):
        self.name = "WhiteNoise"
        self.category = "sources"
        self.type = "white_noise"
        self.summary = "Multi-dimensional Gaussian white noise source."
        self.description = (
            "Generates independent Gaussian noise samples at each simulation step:\n"
            "$$\n"
            "y_i(t) \\sim \\mathcal{N}(\\mu_i, \\sigma_i^2)\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="mean",
                type="scalar | vector | matrix",
                description="Mean value of the noise."
            ),
            ParameterMeta(
                name="std",
                type="scalar | vector | matrix",
                description="Standard deviation of the noise."
            ),
            ParameterMeta(
                name="seed",
                type="int",
                description="Random seed for reproducibility."
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
                description="Gaussian noise output signal."
            )
        ]