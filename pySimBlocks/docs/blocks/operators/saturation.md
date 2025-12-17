# Saturation

## Summary

The **Saturation** block applies element-wise saturation to its input signal,
limiting the output to specified lower and upper bounds.

---

## Mathematical definition

The saturated output is defined as:

$$
y[k] = \mathrm{clip}(u[k], u_{\min}, u_{\max})
$$

where:
- $u[k]$ is the input signal,
- $u_{\min}$ is the lower saturation bound,
- $u_{\max}$ is the upper saturation bound.

---

## Parameters

### `u_min` (optional)

Lower saturation bound.

- Scalar or vector-valued
- Default behavior corresponds to no lower bound

### `u_max` (optional)

Upper saturation bound.

- Scalar or vector-valued
- Default behavior corresponds to no upper bound

### `sample_time` (optional)

Execution period of the block.

If not specified, the simulator time step is used.

---

## Inputs

### `in`

Input signal.

- Dimension: $(n, 1)$

---

## Outputs

### `out`

Saturated output signal.

- Dimension: $(n, 1)$

---

## Notes

- The block has no internal state.
- The block has direct feedthrough.
- Saturation is applied component-wise.
- Scalar bounds are automatically broadcast to match the input dimension.
- Absence of saturation is represented by infinite bounds.
- This block is equivalent to the Simulink **Saturation** block.
