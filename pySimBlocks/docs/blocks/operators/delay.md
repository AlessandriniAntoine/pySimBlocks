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

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `num_delays` | integer | Number of discrete delay steps. Default is 1. | True |
| `initial_output` | scalar or vector | Initial value to fill the delay buffer. If not provided, the buffer is initialized as zero. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `in` | Input signal to be delayed. |

---

## Outputs


| Port | Description |
|------|------------|
| `out` | Delayed output signal. |

---

## Notes

- The block has internal state.
- The block has no direct feedthrough.
- The delay buffer stores the last $N$ input samples.
- Output dimensions are inferred from the first valid input if not explicitly
  initialized.
- This block is equivalent to the Simulink **Delay** / **Unit Delay** block.
