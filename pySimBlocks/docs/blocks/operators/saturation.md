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

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `u_min`     | scalar or vector | Lower saturation bound. If omitted, no lower bound is applied. | True |
| `u_max`     | scalar or vector | Upper saturation bound. If omitted, no upper bound is applied. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `in` | Input signal. |

---

## Outputs

| Port | Description |
|------|------------|
| `out` | Saturated output signal. |

---

## Notes

- The block has no internal state.
- The block has direct feedthrough.
- Saturation is applied component-wise.
- Scalar bounds are automatically broadcast to match the input dimension.
- Absence of saturation is represented by infinite bounds.
- This block is equivalent to the Simulink **Saturation** block.
