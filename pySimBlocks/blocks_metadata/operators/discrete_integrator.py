from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta


class DiscreteIntegratorMeta(BlockMeta):

    def __init__(self):
        self.name = "DiscreteIntegrator"
        self.category = "operators"
        self.type = "discrete_integrator"
        self.summary = "Discrete-time integrator block."
        self.description = (
            "Implements a discrete-time integration of the input signal.\n"
            "The state evolves according to:\n"
            "$$\n"
            "x[k+1] = x[k] + dt \\, u[k]\n"
            "$$\n"
            "with output:\n"
            "$$\n"
            "y[k] = x[k]\n"
            "$$\n"
            "for forward Euler integration."
        )

        self.parameters = [
            ParameterMeta(
                name="initial_state",
                type="scalar | vector | matrix"
            ),
            ParameterMeta(
                name="method",
                type="enum",
                autofill=True,
                default="euler forward",
                enum=["euler forward", "euler backward"]
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
                description="Input signal to integrate."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"],
                description="Integrated output signal."
            )
        ]