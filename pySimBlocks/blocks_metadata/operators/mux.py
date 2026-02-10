from typing import Literal
from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta
from pySimBlocks.gui.model import BlockInstance, PortInstance


class MuxMeta(BlockMeta):

    def __init__(self):
        self.name = "Mux"
        self.category = "operators"
        self.type = "mux"
        self.summary = "Vertical signal concatenation block."
        self.description = (
            "Concatenates multiple input column vectors vertically:\n"
            "$$\n"
            "\\mathrm{out} =\n"
            "\\begin{bmatrix}\n"
            "\\mathrm{in}_1 \\\\\n"
            "\\mathrm{in}_2 \\\\\n"
            "\\vdots \\\\\n"
            "\\mathrm{in}_N\n"
            "\\end{bmatrix}\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="num_inputs",
                type="int",
                autofill=True,
                default=2
            ),
            ParameterMeta(
                name="sample_time",
                type="float"
            )
        ]

        self.inputs = [
            PortMeta(
                name="in",
                display_as="",
                shape=["n", 1],
                description="Input column vectors to concatenate."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["m", 1],
                description="Vertically concatenated output vector."
            )
        ]

    def resolve_port_group(
        self,
        port_meta: PortMeta,
        direction: Literal['input', 'output'],
        instance: "BlockInstance"
    ) -> list["PortInstance"]:

        if direction == port_meta.name == "input":
            num_inputs = instance.parameters.get("num_inputs", 0)
            ports = []
            for i in range(1, num_inputs + 1):
                ports.append(
                    PortInstance(
                        name=f"{port_meta.name}{i}",
                        display_as="",
                        direction="input",
                        block=instance
                    )
                )

            return ports

        return super().resolve_port_group(port_meta, direction, instance)