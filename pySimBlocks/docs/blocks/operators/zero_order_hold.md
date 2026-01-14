# ZeroOrderHold

## Summary

The **ZeroOrderHold** block samples an input signal at discrete instants and
holds the sampled value constant between sampling instants.

---

## Mathematical definition

Let $T_s$ be the sampling period. The output is defined as:

$$
y[k] = u[k_s]
$$

where $k_s$ denotes the most recent sampling instant such that the elapsed
time since $k_s$ is less than $T_s$.

Between two sampling instants, the output remains constant.

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `in` | Input signal to be sampled and held. |

---

## Outputs

| Port | Description |
|------|------------|
| `out` | Output signal that holds the last sampled value. |

---

## Notes

- The block has internal state.
- The block has direct feedthrough.
- The block models sampling and hold behavior only.
- It does not modify the simulator execution rate.
- The held value is updated when the elapsed time since the last sample
  reaches the specified sampling period.
- This block is equivalent to the Simulink **Zero-Order Hold** block.
