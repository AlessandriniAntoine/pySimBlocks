# Sinusoidal

## Summary

The **Sinusoidal** block generates sinusoidal signals with configurable
amplitude, frequency, phase and offset for each output dimension.

---

## Mathematical definition

For each output component $i$, the signal is defined as:

$$
y_i(t) = A_i \sin(2\pi f_i t + \varphi_i) + o_i
$$

where:
- $A_i$ is the amplitude,
- $f_i$ is the frequency in Hertz,
- $\varphi_i$ is the phase shift,
- $o_i$ is the constant offset.

---

## Parameters

### `amplitude`

Sinusoidal amplitude.

- Scalar or vector-valued
- Scalars are broadcast to all dimensions

### `frequency`

Sinusoidal frequency in Hertz.

- Scalar or vector-valued
- Scalars are broadcast to all dimensions

### `phase` (optional)

Phase shift in radians.

- Scalar or vector-valued
- Default value is zero

### `offset` (optional)

Constant offset added to the signal.

- Scalar or vector-valued
- Default value is zero

### `sample_time` (optional)

Execution period of the block.

If not specified, the simulator time step is used.

---

## Inputs

This block has **no inputs**.

---

## Outputs

### `out`

Sinusoidal output signal.

- Dimension: $(n, 1)$

---

## Notes

- The block has no internal state.
- Each output dimension may have its own frequency and phase.
- Scalar parameters are automatically broadcast.
