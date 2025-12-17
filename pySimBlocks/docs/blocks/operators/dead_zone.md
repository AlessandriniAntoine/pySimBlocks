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

### `lower_bound` (optional)

Lower bound of the dead zone.

- Scalar or vector-valued
- Must be less than or equal to zero
- Default value is zero

### `upper_bound` (optional)

Upper bound of the dead zone.

- Scalar or vector-valued
- Must be greater than or equal to zero
- Default value is zero

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

Output signal after dead-zone transformation.

- Dimension: $(n, 1)$

---

## Notes

- The block has no internal state.
- The block has direct feedthrough.
- Bounds are broadcast to match the input dimension when needed.
- The dead zone must always include zero.
- This block is equivalent to the Simulink **Dead Zone** block.
