from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class ExternalInputMeta(BlockMeta):

    def __init__(self):
        self.name = "ExternalInput"
        self.category = "interfaces"
        self.type = "external_input"
        self.summary = "Pass-through block for external real-time measurements."
        self.description = (
            "Pass-through block intended to inject measurements coming from an\n"
            "external real-time application (camera, robot sensors, network, etc.)\n"
            "into a pySimBlocks model.\n\n"
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
                description="External input signal."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["m", 1],
                description="Model data signal."
            )
        ]