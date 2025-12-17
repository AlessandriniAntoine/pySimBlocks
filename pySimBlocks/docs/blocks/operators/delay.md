# Delay

## Summary

The **Delay** block outputs a delayed version of its input signal by a fixed
number of discrete simulation steps.

---

## Mathematical definition

For a delay of $N$ steps, the block implements:

$$
y[k] = u[k - N]
$$

where:
- $u[k]$ is the input signal,
- $y[k]$ is the delayed output signal.

---

## Parameters

### `num_delays` (optional)

Number of discrete delay steps $N$.

- Must be an integer greater than or equal to 1
- Default value is 1

### `initial_output` (optional)

Initial value used to fill the delay buffer.

- Scalar or vector-valued
- If not provided:
  - the buffer is initialized from the input if available at initialization,
  - otherwise the dimension is inferred at the first simulation step

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

Delayed output signal.

- Dimension: $(n, 1)$

---

## Notes

- The block has internal state.
- The block has no direct feedthrough.
- The delay buffer stores the last $N$ input samples.
- Output dimensions are inferred from the first valid input if not explicitly
  initialized.
- This block is equivalent to the Simulink **Delay** / **Unit Delay** block.
