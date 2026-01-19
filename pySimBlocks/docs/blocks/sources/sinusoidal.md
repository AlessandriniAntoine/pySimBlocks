# Sinusoidal

## Summary

The **Sinusoidal** block generates sinusoidal signals with configurable
amplitude, frequency, phase and offset for each output dimension.

---

## Mathematical definition

For each output component $i$, the signal is defined as:

$$
y_i(t) = A_i \sin(2\pi f_i t + \varphi_i) + o_i
$$

where:
- $A_i$ is the amplitude,
- $f_i$ is the frequency in Hertz,
- $\varphi_i$ is the phase shift,
- $o_i$ is the constant offset.

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `amplitude` | scalar or vector or matrix | Sinusoidal amplitude. Can be a scalar or vector. | False |
| `frequency` | scalar or vector or matrix | Sinusoidal frequency in Hertz. Can be a scalar or vector. | False |
| `phase` | scalar or vector or matrix | Phase shift in radians. Default is zero. | True |
| `offset` | scalar or vector or matrix | Constant offset added to the signal. Default is zero. | True |
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
- Each output dimension may have its own frequency and phase.
- Scalar parameters are automatically broadcast.
