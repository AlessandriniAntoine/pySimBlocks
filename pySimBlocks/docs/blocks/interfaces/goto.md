# Goto

## Summary

Publishes its input signal to the global signal bus under a named tag. Used together with the [BusFrom](bus_from.md) block to connect distant parts of a model without drawing an explicit wire.

## Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | yes | Unique name of the block instance. |
| `tag` | `str` | yes | Signal bus tag under which the input is published. Must match the `tag` of the corresponding BusFrom block(s). |
| `sample_time` | `float` or `None` | no | Sampling period in seconds. If `None`, the global simulation `dt` is used. |

## Inputs

| Port | Description |
|---|---|
| `in` | Signal to publish on the bus. |

## Outputs

None. The signal is read through a BusFrom block with the same tag.

## Description

At each time step, the block writes its input to the signal bus:

```
bus[tag] = in
```

A Goto block and the BusFrom blocks sharing its tag form a virtual connection. Although no wire is drawn between them, the model's topological sort adds a hidden dependency from each Goto to every BusFrom with the same tag. The Goto is therefore always executed before its consumers within the same time step.

The block has direct feedthrough and carries no internal state.

At initialization, the current input is published to the bus. If no input is connected yet, the bus entry is set to `None`.

## Notes

- The Goto block has no output port, so it cannot be used as a source for another block.
- A tag is a plain string. Use clear names (for example `"reference"` or `"measure"`) to keep large diagrams readable.
- Each tag should be published by a single Goto block. Several BusFrom blocks can read the same tag.

## Example

```python
from pySimBlocks import Model
from pySimBlocks.blocks.sources import Constant
from pySimBlocks.blocks.interfaces import Goto, BusFrom

model = Model("example")
model.add_block(Constant("ref", value=1.0))
model.add_block(Goto("ref_goto", tag="reference"))
model.add_block(BusFrom("ref_from", tag="reference"))

model.connect("ref", "out", "ref_goto", "in")
# "ref_from.out" now carries the value of "ref.out".
```
