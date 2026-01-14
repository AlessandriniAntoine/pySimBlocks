# LinearStateSpace

## Summary

The **LinearStateSpace** block implements a discrete-time linear state-space system without direct feedthrough.

---

## Mathematical definition

The system is defined by the equations:

$$
x[k+1] = A x[k] + B u[k]
$$

$$
y[k] = C x[k]
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
- The system is strictly proper (no direct feedthrough).
- Matrix $D$ is intentionally not supported to avoid algebraic loops.
- The output is computed from the current state.
