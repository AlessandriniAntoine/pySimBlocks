from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class StepMeta(BlockMeta):

    def __init__(self):
        self.name = "Step"
        self.category = "sources"
        self.type = "step"
        self.summary = "Step signal source."
        self.description = (
            "Generates a step signal defined by:\n"
            "$$\n"
            "y(t) =\n"
            "\\begin{cases}\n"
            "y_{\\text{before}}, & t < t_0 \\\\\n"
            "y_{\\text{after}},  & t \\geq t_0\n"
            "\\end{cases}\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="value_before",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=[[0.0]],
                description="Output value before the step time."
            ),
            ParameterMeta(
                name="value_after",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=[[1.0]],
                description="Output value after the step time."
            ),
            ParameterMeta(
                name="start_time",
                type="float",
                required=True,
                autofill=True,
                default=1.0,
                description="Time at which the step occurs."
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
                description="Step output signal."
            )
        ]