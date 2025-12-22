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

- **controller**: Selects the controller structure: `P`, `I`, `PI`, `PD`, or `PID`.

- **Kp, Ki, Kd**: Proportional, integral, and derivative gains. All gains must be scalar-like.

- **integration_method**: Numerical integration scheme for the integral term:
  - `euler forward`
  - `euler backward`

- **u_min, u_max**: Optional output saturation bounds. When enabled, an anti-windup mechanism clamps the integral state.

- **sample_time**: Optional block-specific sample time.

---

## Inputs

- **e**: Control error signal.

---

## Outputs

- **u**: Control command.

---

## Notes

- The block is strictly SISO.
- Dimension checks are enforced at runtime.
- Direct feedthrough depends on the controller structure and integration method.
