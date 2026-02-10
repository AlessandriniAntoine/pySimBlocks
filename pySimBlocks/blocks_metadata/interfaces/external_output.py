from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class ExternalOutputMeta(BlockMeta):

    def __init__(self):
        self.name = "ExternalOutput"
        self.category = "interfaces"
        self.type = "external_output"
        self.summary = "Pass-through block for external real-time commands/values."
        self.description = (
            "Pass-through block intended to expose a model command/value to an\n"
            "external real-time application (motors, network, hardware driver, etc.).\n\n"
            "This block does not perform any synchronization. It only enforces the\n"
            "pySimBlocks signal convention (column vectors of shape (n,1))."
        )

        self.parameters = [
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
                description="Model command/value signal."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["m", 1],
                description="External output signal."
            )
        ]