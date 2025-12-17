# Constant

## Summary

The **Constant** block generates a signal with a fixed value over time.
The output does not depend on time, system state, or any input signal.

---

## Mathematical definition

The block computes:

$$
y(t) = c
$$

where $c$ is a constant scalar or vector value.

---

## Parameters

### `value`

Constant output value.

- Can be a scalar or a vector
- Internally converted to a column vector

### `sample_time` (optional)

Execution period of the block.

If not provided, the simulator time step is used.

---

## Inputs

This block has **no inputs**.

---

## Outputs

### `out`

Constant output signal.

- Dimension: $(n, 1)$
- Holds the same value for the entire simulation

---

## Notes

- The block has no internal state.
- The output value is copied at each simulation step.
- This block is typically used as a reference or bias source.
