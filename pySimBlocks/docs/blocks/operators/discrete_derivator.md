# DiscreteDerivator

## Summary

The **DiscreteDerivator** block estimates the discrete-time derivative of an
input signal using a backward finite-difference scheme.

---

## Mathematical definition

The derivative is approximated as:

$$
y[k] = \frac{u[k] - u[k-1]}{dt}
$$

where:
- $u[k]$ is the current input sample,
- $u[k-1]$ is the previous input sample,
- $dt$ is the simulation time step.

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `initial_output` | scalar or vector or matrix | Initial value to fill the delay buffer. If not provided, the buffer is initialized as zero. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `in` | Input signal for derivative estimation. |

---

## Outputs

| Port | Description |
|------|------------|
| `out` | Estimated discrete-time derivative of the input signal. |

---

## Notes

- The block has internal state.
- The block has direct feedthrough.
- A backward difference scheme is used because future input values are not
  accessible.
- Input dimension changes between steps are not allowed.
- This block matches Simulink **Derivative** behavior in discrete-time mode.
