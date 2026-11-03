# BusFrom

## Summary

Reads a signal from the global signal bus by tag. It is the counterpart of the [Goto](goto.md) block and allows a signal to be reused elsewhere in the model without drawing an explicit wire.

## Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | yes | Unique name of the block instance. |
| `tag` | `str` | yes | Signal bus tag to read from. Must match the `tag` of a Goto block in the same model. |
| `sample_time` | `float` or `None` | no | Sampling period in seconds. If `None`, the global simulation `dt` is used. |

## Inputs

None. The value is read from the signal bus.

## Outputs

| Port | Description |
|---|---|
| `out` | Value published on the bus under `tag`. |

## Description

At each time step, the block reads the value stored on the signal bus:

```
out = bus[tag]
```

A Goto block and the BusFrom blocks sharing its tag form a virtual connection. Although no wire is drawn between them, the model's topological sort adds a hidden dependency from each Goto to every BusFrom with the same tag. The Goto is therefore always executed before the BusFrom within the same time step.

The block has direct feedthrough and carries no internal state.

At initialization, the output is read from the bus if the tag is already present. Otherwise, it is set to `None`.

## Errors

If no Goto block has written the tag to the bus when the output is updated, the block raises a `KeyError` naming the missing tag. Check that a Goto block with the same tag exists in the model.

## Notes

- Several BusFrom blocks can read the same tag.
- The tag must match exactly, including case.
- In the GUI, this block appears as **BusFrom** in the *interfaces* category, next to Goto.

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
