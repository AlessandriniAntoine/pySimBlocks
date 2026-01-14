# SofaExchangeIO

## Summary

The **SofaExchangeIO** block provides an interface between a pySimBlocks model
and an external SOFA controller by exposing dynamic input and output ports.

---

## Description

This block does **not** execute a SOFA simulation.
It must **only** be used when SOFA will be running the simulation loop.
It acts only as a data exchange interface between:

- a pySimBlocks control model, and
- a SOFA controller that provides inputs and consumes outputs.

The block is fully stateless and does not modify the signals it exchanges.

---

## Parameters

| Name | Type | Description | Required |
|------|------|-------------|----------|
| `scene_file` | string | Path to the SOFA scene file to be simulated. | Yes |
| `input_keys` | list[string] | Names of the input ports $ u_1, \dots, u_m $. | Yes |
| `output_keys` | list[string] | Names of the output ports returned by the output function. | Yes |
| `sample_time` | float | Execution period of the block. If omitted, the global simulation time step is used. | No | 

---

## Inputs

Inputs are dynamically defined by `input_keys`.

- Each input must be connected.
- Each input is a NumPy array of shape (n, 1).
- Each input corresponds to a command sent to the SOFA controller.

---

## Outputs

Outputs are dynamically defined by `output_keys`.

- Each output is a NumPy array of shape (n, 1).
- Each output corresponds to a measurement extracted from the SOFA scene.
- Each output is produced by the pySimBlocks controller logic.

---

## Notes

- This block does not run a SOFA simulation.
- It is intended to be embedded inside a SOFA controller.
- The block has no internal state.
- All data validation is performed at runtime.
