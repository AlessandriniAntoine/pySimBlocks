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

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `value` | scalar or vector or matrix | Constant output value. Can be a scalar or vector. | False |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

This block has **no inputs**.

---

## Outputs

| Port | Description |
|------|------------|
| `out` | Constant output signal. |

---

## Notes

- The block has no internal state.
- The output value is copied at each simulation step.
- This block is typically used as a reference or bias source.
