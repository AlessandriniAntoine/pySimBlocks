# SofaExchangeIO

## Summary

The **SofaExchangeIO** block provides an interface between a pySimBlocks model
and an external SOFA controller by exposing dynamic input and output ports.

---

## Description

This block does **not** execute a SOFA simulation.
It acts only as a data exchange interface between:

- a pySimBlocks control model, and
- a SOFA controller that provides inputs and consumes outputs.

The block is fully stateless and does not modify the signals it exchanges.

---

## Parameters

### `input_keys`

List of names of input signals provided by the external SOFA controller.

Each key creates a dynamic input port.

### `output_keys`

List of names of output signals consumed by the SOFA controller.

Each key creates a dynamic output port.

### `scene_file` (optional)

Path to the SOFA scene file.

This parameter is used only for automatic code or scene generation.

### `sample_time` (optional)

Execution period of the block.

If not specified, the simulator time step is used.

---

## Inputs

Dynamic inputs defined by `input_keys`.

Each input is expected to be a column vector.

---

## Outputs

Dynamic outputs defined by `output_keys`.

Each output is produced by the pySimBlocks controller logic.

---

## Notes

- This block does not run a SOFA simulation.
- It is intended to be embedded inside a SOFA controller.
- The block has no internal state.
- All data validation is performed at runtime.
