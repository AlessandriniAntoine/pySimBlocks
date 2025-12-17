# Step

## Summary

The **Step** block generates a signal that switches from an initial value
to a final value at a specified time.

---

## Mathematical definition

The step signal is defined as:

$$
y(t) =
\begin{cases}
y_{\text{before}}, & t < t_0 \\
y_{\text{after}},  & t \geq t_0
\end{cases}
$$

where:
- $y_{\text{before}}$ is the value before the step,
- $y_{\text{after}}$ is the value after the step,
- $t_0$ is the step time.

---

## Parameters

### `value_before`

Output value before the step time.

- Scalar or vector-valued
- Scalars are broadcast to all dimensions

### `value_after`

Output value after the step time.

- Scalar or vector-valued
- Must have the same dimension as `value_before`

### `start_time`

Time at which the step occurs.

### `sample_time` (optional)

Execution period of the block.

If not specified, the simulator time step is used.

---

## Inputs

This block has **no inputs**.

---

## Outputs

### `out`

Step output signal.

- Dimension: $(n, 1)$

---

## Notes

- The block has no internal state.
- A small numerical tolerance is used to ensure consistent switching
  behavior on discrete time grids.
- This block is typically used to generate reference signals.
