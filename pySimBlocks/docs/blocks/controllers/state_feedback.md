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

### `K`

State feedback gain matrix.

### `G`

Reference feedforward gain matrix.

### `sample_time` (optional)

Execution period of the block.

If not specified, the simulator time step is used.

---

## Inputs

### `r`

Reference vector.

- Dimension: $(p, 1)$

### `x`

State measurement vector.

- Dimension: $(n, 1)$

---

## Outputs

### `u`

Control input vector.

- Dimension: $(m, 1)$

---

## Notes

- The controller has no internal state.
- The control law is evaluated at each simulation step.
- Both reference and state inputs must be connected.
