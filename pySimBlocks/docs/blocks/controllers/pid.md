# PID Controller

## Description

The PID block implements a discrete-time proportional–integral–derivative
controller in parallel form. It is strictly single-input single-output (SISO)
and follows Simulink-like execution semantics.

The controller structure can be configured to enable or disable individual
terms (P, I, D), and the integration method can be selected.

---

## Mathematical Formulation

The control law is given by:

$$
u[k] = K_p e[k] + x_i[k] + K_d \frac{e[k] - e[k-1]}{dt}
$$

where the integral state evolves according to:

### Euler forward integration

$$
x_i[k+1] = x_i[k] + K_i e[k] \, dt
$$

### Euler backward integration

$$
x_i[k+1] = u[k] - \left( K_p e[k] + K_d \frac{e[k] - e[k-1]}{dt} \right)
$$

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `controller` | string | Controller structure: `P`, `I`, `PI`, `PD`, or `PID`. | False |
| `Kp` | scalar | Proportional gain. | False |
| `Ki` | scalar | Integral gain. | False |
| `Kd` | scalar | Derivative gain. | False |
| `integration_method` | string | Numerical integration scheme for the integral term: `euler forward` (default) or `euler backward`. | True |
| `u_min` | scalar | Minimum output saturation bound. | True |
| `u_max` | scalar | Maximum output saturation bound. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `e` | Control error. |

---

## Outputs


| Port | Description |
|------|------------|
| `u` | Control command. |

---

## Notes

- The block is strictly SISO.
- Dimension checks are enforced at runtime.
- Direct feedthrough depends on the controller structure and integration method.

© 2026 The pySimBlocks Authors – Licensed under LGPL-3.0-or-later
