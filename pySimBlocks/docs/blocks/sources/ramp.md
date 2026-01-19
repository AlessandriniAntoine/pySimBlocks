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

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `slope` | scalar or vector or matrix | Ramp slope for each output dimension. Scalars are broadcast to all dimensions. | False |
| `start_time` | scalar or vector or matrix | Time at which the ramp starts. Default is zero. | True |
| `offset` | scalar or vector or matrix | Output value before the ramp starts. Default is zero. | True |
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
- Each output dimension may have a different slope and start time.
- Scalar parameters are automatically broadcast.
