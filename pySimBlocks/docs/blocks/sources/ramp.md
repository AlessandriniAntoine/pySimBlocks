# Ramp

## Summary

The **Ramp** block generates a ramp signal for each output dimension.
Each ramp starts at a specified time with a given slope and initial offset.

---

## Mathematical definition

For each output component $i$, the signal is defined as:

$$
y_i(t) = o_i + s_i \max(0, t - t_{0,i})
$$

where:
- $s_i$ is the slope,
- $t_{0,i}$ is the start time,
- $o_i$ is the initial offset.

---

## Parameters

### `slope`

Ramp slope for each output dimension.

- Scalar or vector-valued
- Scalars are broadcast to all dimensions

### `start_time` (optional)

Time at which the ramp starts.

- Scalar or vector-valued
- Default value is zero

### `offset` (optional)

Output value before the ramp starts.

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

Ramp output signal.

- Dimension: $(n, 1)$

---

## Notes

- The block has no internal state.
- Each output dimension may have a different slope and start time.
- Scalar parameters are automatically broadcast.
