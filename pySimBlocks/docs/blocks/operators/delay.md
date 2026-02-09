# Delay

## Summary

The **Delay** block outputs a delayed version of its input signal by a fixed
number of discrete simulation steps.

The block can be reset to an initial output value via an optional reset input.
This reset is a level-triggered signal: when the reset input is true (non-zero), the delay buffer is reset to the initial output value.
It is not a rising-edge or falling-edge trigger.

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
| `initial_output` | scalar or vector or matrix | Initial value to fill the delay buffer. If not provided, the buffer is initialized as zero. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `in` | Input signal to be delayed. |
| `reset` | Optional reset signal. When true (non-zero), the delay buffer is reset to the initial output value. |

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
- Policy:
    + Signals are 2D arrays.
    + Buffer always exists (never None).
    + Shape is fixed either:
        * immediately if initial_output is non-scalar 2D (shape != (1,1))
        * otherwise at the first non-None input seen by the block
    + If buffer is still "unfixed" and currently scalar (1,1), it can be
      broadcast ONCE to match the first input shape.
    + After shape is fixed, any shape mismatch raises.


---
© 2026 Université de Lille & INRIA – Licensed under LGPL-3.0-or-later
