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

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `value_before` | scalar or vector or matrix | Output value before the step time. Scalars are broadcast to all dimensions. | False |
| `value_after` | scalar or vector or matrix | Output value after the step time. Must have the same dimension as `value_before`. | False |
| `start_time` | float | Time at which the step occurs. | False |
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
- A small numerical tolerance is used to ensure consistent switching
  behavior on discrete time grids.
- This block is typically used to generate reference signals.
