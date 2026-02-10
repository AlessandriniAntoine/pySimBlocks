from typing import Literal
from pySimBlocks.blocks_metadata.block_meta import BlockMeta, ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta
from pySimBlocks.gui.model import BlockInstance, PortInstance


class AlgebraicFunctionMeta(BlockMeta):

    def __init__(self):
        self.name = "Algebraic Function"
        self.category = "operators"
        self.type = "algebraic_function"
        self.summary = "User-defined stateless algebraic function implemented in Python."
        self.description = (
            "This block evaluates a user-provided Python function of the form:\n\n"
            "    y = g(t, dt, u1, u2, ...)\n\n"
            "The function is loaded from an external Python file and executed at each\n"
            "simulation step. Input and output ports are explicitly declared via\n"
            "`input_keys` and `output_keys`.\n\n"
            "This block is stateless and has direct feedthrough."
        )

        self.parameters = [
            ParameterMeta(
                name="file_path",
                type="string",
                required=True,
                description="Path to the Python file containing the function relative to the parameters.yaml file."
            ),
            ParameterMeta(
                name="function_name",
                type="string",
                required=True,
                description="Name of the function to call inside the Python file."
            ),
            ParameterMeta(
                name="input_keys",
                type="list[string]",
                required=True,
                description="List of input port names. These must match the function arguments after (t, dt)."
            ),
            ParameterMeta(
                name="output_keys",
                type="list[string]",
                required=True,
                description="List of output port names. The function must return a dict with exactly these keys."
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
                description="Optional execution period of the block."
            ),
        ]

        self.inputs = [
            PortMeta(
                name="in",
                display_as="",
                shape=[],
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="",
                shape=[],
            )
        ]

    def resolve_port_group(
        self,
        port_meta: PortMeta,
        direction: Literal['input', 'output'],
        instance: "BlockInstance"
    ) -> list["PortInstance"]:

        ports = []
        if direction == "input":
            keys = instance.parameters.get("input_keys", [])
            if keys is None:
                return []
            for key in keys:
                ports.append(
                    PortInstance(
                        name=f"{key}",
                        display_as=key,
                        direction="input",
                        block=instance
                    )
                )
            return ports

        elif direction == "output":
            keys = instance.parameters.get("output_keys", [])
            if keys is None:
                return []
            for key in keys:
                ports.append(
                    PortInstance(
                        name=f"{key}",
                        display_as=key,
                        direction="output",
                        block=instance
                    )
                )
            return ports

        return super().resolve_port_group(port_meta, direction, instance)