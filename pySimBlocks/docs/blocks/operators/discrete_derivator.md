# DiscreteDerivator

## Summary

The **DiscreteDerivator** block estimates the discrete-time derivative of an
input signal using a backward finite-difference scheme.

---

## Mathematical definition

The derivative is approximated as:

$$
y[k] = \frac{u[k] - u[k-1]}{dt}
$$

where:
- $u[k]$ is the current input sample,
- $u[k-1]$ is the previous input sample,
- $dt$ is the simulation time step.

---

## Parameters

### `initial_output` (optional)

Initial derivative value at the first simulation step.

- Scalar or vector-valued
- If not provided, the derivative is initialized to zero when the first input
  becomes available

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

Estimated discrete-time derivative.

- Dimension: $(n, 1)$

---

## Notes

- The block has internal state.
- The block has direct feedthrough.
- A backward difference scheme is used because future input values are not
  accessible.
- Input dimension changes between steps are not allowed.
- This block matches Simulink **Derivative** behavior in discrete-time mode.
