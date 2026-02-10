# StateFeedback

## Summary

The **StateFeedback** block implements a discrete-time static state-feedback
controller combining reference feedforward and state feedback.

---

## Mathematical definition

The control law is defined as:

$$
u[k] = G r[k] - K x[k]
$$

where:
- $r[k]$ is the reference vector,
- $x[k]$ is the measured state vector,
- $u[k]$ is the control input.

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `K` | array | State feedback gain matrix. | False |
| `G` | array | Reference feedforward gain matrix. | False |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `r` | Reference vector. |
| `x` | State measurement vector. |

---

## Outputs

| Port | Description |
|------|------------|
| `u` | Control input vector. |

---

## Notes

- The controller has no internal state.
- The control law is evaluated at each simulation step.
- Both reference and state inputs must be connected.


---
© 2026 Université de Lille & INRIA – Licensed under LGPL-3.0-or-later
