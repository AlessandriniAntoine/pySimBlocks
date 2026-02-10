from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class RateLimiterMeta(BlockMeta):

    def __init__(self):
        self.name = "RateLimiter"
        self.category = "operators"
        self.type = "rate_limiter"
        self.summary = "Discrete-time rate limiter block."
        self.description = (
            "Limits the rate of change of the output signal according to:\n"
            "$$\n"
            "\\Delta u = u[k] - y[k-1]\n"
            "$$\n"
            "$$\n"
            "y[k] = y[k-1] + \\mathrm{clip}(\\Delta u,\\; s^{-} dt,\\; s^{+} dt)\n"
            "$$\n"
            "where $s^{+}$ is the rising slope and $s^{-}$ is the falling slope."
        )

        self.parameters = [
            ParameterMeta(
                name="rising_slope",
                type="scalar | vector | matrix"
            ),
            ParameterMeta(
                name="falling_slope",
                type="scalar | vector | matrix"
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
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"],
                description="Rate-limited output signal."
            )
        ]