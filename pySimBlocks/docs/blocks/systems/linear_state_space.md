# LinearStateSpace

## Summary

The **LinearStateSpace** block implements a discrete-time linear state-space system.

Without feedthrough matrix $D$ the system is strictly proper. When $D$ is provided
the block has direct feedthrough and $y[k]$ depends on $u[k]$ at the same step.

---

## Mathematical definition

Without $D$ (strictly proper):

$$
x[k+1] = A x[k] + B u[k]
$$

$$
y[k] = C x[k]
$$

With $D$ (direct feedthrough):

$$
x[k+1] = A x[k] + B u[k]
$$

$$
y[k] = C x[k] + D u[k]
$$

where:
- $x[k]$ is the state vector,
- $u[k]$ is the input vector,
- $y[k]$ is the output vector.

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `A` | 2D array | State transition matrix of size (n, n). | False |
| `B` | 2D array | Input matrix of size (n, m). | False |
| `C` | 2D array | Output matrix of size (p, n). | False |
| `D` | 2D array | Feedthrough matrix of size (p, m). If omitted, no direct feedthrough. | True |
| `x0` | 1D array | Initial state vector of size (n,). If omitted, the state is initialized to zero. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `u` | Input vector. |

---

## Outputs

| Port | Description |
|------|------------|
| `x` | State vector. |
| `y` | Output vector. |

---

## Notes

- The block has internal state.
- When `D` is omitted or `None`, the system is strictly proper (no direct feedthrough).
- When `D` is provided, the block has direct feedthrough: `y[k]` depends on `u[k]`
  at the same simulation step.
- A block with direct feedthrough cannot be part of a feedback loop without a `Delay`
  block breaking the cycle — pySimBlocks will raise a `RuntimeError` at compile time
  if an algebraic loop is detected.


---
© 2026 Université de Lille & INRIA – Licensed under LGPL-3.0-or-later
