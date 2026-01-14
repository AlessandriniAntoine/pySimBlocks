# Luenberger

## Summary

The **Luenberger** block implements a discrete-time state observer that
estimates the system state from input and output measurements.

---

## Mathematical definition

The observer is defined by the equations:

$$
x̂[k+1] = A x̂[k] + B u[k] + L (y[k] - C x̂[k])
$$

$$
ŷ[k] = C x̂[k]
$$

where:
- $x̂[k]$ is the estimated state,
- $u[k]$ is the control input,
- $y[k]$ is the measured output,
- $ŷ[k]$ is the estimated output.

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `A` | array | System state matrix. | False |
| `B` | array | Input matrix. | False |
| `C` | array | Output matrix. | False |
| `L` | array | Observer gain matrix. | False |
| `x0` | array | Initial estimated state. If omitted, the estimate is initialized to zero. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `u` | Control input. |
| `y` | Measured output. |

---

## Outputs

| Port | Description |
|------|------------|
| `x_hat` | Estimated state. |
| `y_hat` | Estimated output. |

---

## Notes

- The block has internal state.
- The observer has no direct feedthrough.
- Matrix $D$ is intentionally not supported to avoid algebraic loops.
- The state estimate is updated once per simulation step.
