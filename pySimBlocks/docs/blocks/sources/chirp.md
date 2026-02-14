# Chirp

## Summary

The **Chirp** block generates a frequency-swept sinusoidal signal
(linear or logarithmic) with configurable amplitude, phase, offset,
start time, and duration.

---

## Mathematical definition

For each output component $i$:

$$
y_i(t) = A_i \sin(\phi_i(t)) + o_i
$$

with parameters:
- $A_i$: amplitude,
- $o_i$: offset,
- $\phi_i(t)$: chirp phase,
- $f_{0,i}$: initial frequency,
- $f_{1,i}$: final frequency,
- $T_i$: chirp duration,
- $t_{0,i}$: chirp start time,
- $\varphi_i$: initial phase.

Define:
$$
\tau_i = \max(0, t - t_{0,i}), \quad
\tau_{c,i} = \min(\tau_i, T_i)
$$

Linear mode:
$$
k_i = \frac{f_{1,i} - f_{0,i}}{T_i}
$$
$$
\phi_i(t) =
2\pi\left(f_{0,i}\tau_{c,i} + \frac{1}{2}k_i\tau_{c,i}^2\right)
+ 2\pi f_{1,i}\max(0, \tau_i - T_i)
+ \varphi_i
$$

Log mode:
$$
r_i = \frac{f_{1,i}}{f_{0,i}}
$$
$$
\phi_i(t) =
\frac{2\pi f_{0,i}T_i}{\ln(r_i)}
\left(r_i^{\tau_{c,i}/T_i} - 1\right)
+ 2\pi f_{1,i}\max(0, \tau_i - T_i)
+ \varphi_i
$$

After duration, phase continuity is preserved and oscillation continues at $f_1$.

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `amplitude` | scalar or vector or matrix | Signal amplitude. Scalars are broadcast to all dimensions. | False |
| `f0` | scalar or vector or matrix | Initial frequency in Hertz. Scalars are broadcast. | False |
| `f1` | scalar or vector or matrix | Final frequency in Hertz. Scalars are broadcast. | False |
| `duration` | scalar or vector or matrix | Sweep duration in seconds. Must be strictly positive. Scalars are broadcast. | False |
| `start_time` | scalar or vector or matrix | Start time in seconds. Before this time, sweep is not active. Default is `0.0`. | True |
| `offset` | scalar or vector or matrix | Constant offset added to output. Default is `0.0`. | True |
| `phase` | scalar or vector or matrix | Initial phase in radians. Default is `0.0`. | True |
| `mode` | string | Sweep mode: `linear` or `log`. Default is `linear`. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

This block has **no inputs**.

---

## Outputs

| Port | Description |
|------|------------|
| `out` | Chirp output signal. |

---

## Notes

- The block has no internal state.
- All array-like parameters must have compatible shapes.
- Scalar parameters are broadcast to the common signal shape.
- In `log` mode, `f0 > 0`, `f1 > 0`, and `f0 != f1` are required.
- The output keeps oscillating after `duration` at frequency `f1`.


---
© 2026 Université de Lille & INRIA – Licensed under LGPL-3.0-or-later
