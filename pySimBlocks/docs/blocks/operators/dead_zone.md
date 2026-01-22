# DeadZone

## Summary

The **DeadZone** block applies a dead-zone nonlinearity to its input signal.
Values within a specified interval around zero are suppressed, while values
outside the interval are shifted accordingly.

---

## Mathematical definition

For each output component $i$, the signal is defined as:

$$
y_i =
\begin{cases}
0 & \text{if } u_{\min,i} \le u_i \le u_{\max,i} \\
u_i - u_{\max,i} & \text{if } u_i > u_{\max,i} \\
u_i - u_{\min,i} & \text{if } u_i < u_{\min,i}
\end{cases}
$$

where:
- $u_{\min,i}$ is the lower bound of the dead zone,
- $u_{\max,i}$ is the upper bound of the dead zone.


---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `lower_bound` | scalar or vector or matrix | Lower bound of the dead zone. Must be less than or equal to zero. Default is zero. | True |
| `upper_bound` | scalar or vector or matrix | Upper bound of the dead zone. Must be greater than or equal to zero. Default is zero. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `in` | Input signal to be processed. |

---

## Outputs

| Port | Description |
|------|------------|
| `out` | Output signal after dead-zone transformation. |

---

## Notes

- The block has no internal state.
- The block has direct feedthrough.
- Bounds are broadcast to match the input dimension when needed.
- The dead zone must always include zero.
- This block is equivalent to the Simulink **Dead Zone** block.

© 2026 The pySimBlocks Authors – Licensed under LGPL-3.0-or-later
