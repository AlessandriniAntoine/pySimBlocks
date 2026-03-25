# Adding a New Block

## Overview

Adding a block to pySimBlocks requires creating or modifying three things:

- `pySimBlocks/blocks/<category>/my_block.py` — the core simulation logic
- `pySimBlocks/gui/blocks/<category>/my_block.py` — the GUI metadata
- `pySimBlocks/project/pySimBlocks_blocks_index.yaml` — the block registry entry

The core and GUI layers are fully independent. The core block runs without
the GUI and the GUI block contains no simulation logic.

For a detailed description of the block interface, see {doc}`block_model`.

## Core block

Place the file in the sub-package matching the block's category
(`sources`, `operators`, `controllers`, etc.). The filename must be the
class name in snake_case.

A core block must:

- inherit from {py:class}`~pySimBlocks.core.block.Block`
- declare all input and output ports in `__init__`
- set `direct_feedthrough` at class level
- implement `initialize()` and `output_update()`
- implement `state_update()` if the block has internal state
- use `sample_time=None` to inherit the global `dt`

The following example implements a `ScalarGain` block that multiplies its
input by a constant:
```python
import numpy as np
from pySimBlocks.core.block import Block

class ScalarGain(Block):

    direct_feedthrough = True

    def __init__(self, name: str, gain: float, sample_time: float | None = None):
        super().__init__(name, sample_time)
        self.gain = float(gain)
        self.inputs["in"] = None
        self.outputs["out"] = None

    def initialize(self, t0: float) -> None:
        self.outputs["out"] = np.zeros((1, 1))

    def output_update(self, t: float, dt: float) -> None:
        self.outputs["out"] = self.gain * self.inputs["in"]

    def state_update(self, t: float, dt: float) -> None:
        pass
```

Register it in `pySimBlocks/blocks/operators/__init__.py`:
```python
from .scalar_gain import ScalarGain
```

## GUI block

Place the file in `pySimBlocks/gui/blocks/<category>/my_block.py`.
The class name must be the `myBlockMeta`. It must inherit from
{py:class}`~pySimBlocks.gui.blocks.block_meta.BlockMeta` and declare the
following class attributes in `__init__`:

- `name` — user-facing block name
- `category` — must match the core block category
- `type` — stable identifier used in `project.yaml` (snake_case)
- `summary` — one-line description shown in the block list
- `description` — rich text shown in the block dialog (Markdown, supports LaTeX)
- `inputs` — list of {py:class}`~pySimBlocks.gui.blocks.port_meta.PortMeta`
- `outputs` — list of {py:class}`~pySimBlocks.gui.blocks.port_meta.PortMeta`
- `parameters` — list of {py:class}`~pySimBlocks.gui.blocks.parameter_meta.ParameterMeta`

### Minimal

The following example is the GUI counterpart of the `ScalarGain` block:
```python
from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta

class ScalarGainMeta(BlockMeta):

    def __init__(self):
        self.name = "ScalarGain"
        self.category = "operators"
        self.type = "scalar_gain"
        self.summary = "Multiplies input by a scalar constant."
        self.description = (
            "Computes:\n"
            "$$\n"
            "y = K \\cdot u\n"
            "$$\n"
        )
        self.inputs = [
            PortMeta(name="in", display_as="in", shape=["n", "m"])
        ]
        self.outputs = [
            PortMeta(name="out", display_as="out", shape=["n", "m"])
        ]
        self.parameters = [
            ParameterMeta(name="gain", type="float", required=True, default=1.0),
            ParameterMeta(name="sample_time", type="float"),
        ]
```

### Conditional parameters

Override `is_parameter_active()` to show or hide parameters depending on
the current block configuration. It receives the parameter name and the
current instance parameters, and returns `True` if the parameter should
be visible.

The following example hides `Ki` unless the selected controller includes
an integral term:
```python
def is_parameter_active(self, param_name: str, instance_params: dict) -> bool:
    if param_name == "Ki":
        return instance_params.get("controller") in ["I", "PI", "PID"]
    return super().is_parameter_active(param_name, instance_params)
```

### Dynamic ports and custom dialogs
```{tip}
For dynamic ports (ports whose number depends on a parameter), override
`resolve_port_group()`. For a complete example see
{py:class}`~pySimBlocks.gui.blocks.operators.algebraic_function.AlgebraicFunctionMeta`.

For fully custom dialog layouts (file pickers, extra buttons), override
`build_param()` and/or `build_post_param()`. See the same class for reference.
```

## Registering in the index

Once the core block is registered in its `__init__.py`, run:
```bash
pysimblocks update
```

This regenerates `pySimBlocks/project/pySimBlocks_blocks_index.yaml`
automatically. The new block is then available in the GUI block list and
the project loader.
