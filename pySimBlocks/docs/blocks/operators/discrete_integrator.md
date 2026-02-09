# DiscreteIntegrator

## Summary

The **DiscreteIntegrator** block integrates an input signal over time using
a discrete-time numerical integration scheme.

---

## Mathematical definition

The integrator state evolves according to:

$$
x[k+1] = x[k] + dt * u[k]
$$

The output depends on the selected integration method.

### Euler forward

$$
y[k] = x[k]
$$

### Euler backward

$$
y[k] = x[k] + dt * u[k]
$$

where:
- $u[k]$ is the input signal,
- $x[k]$ is the internal integrated state,
- $dt$ is the simulation time step.

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `initial_state` | scalar or vector or matrix | Initial value of the integrated state. If omitted, the state is initialized as a zero vector. | True |
| `method` | string | Numerical integration method: `euler forward` or `euler backward`. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `in` | Input signal to be integrated. |

---

## Outputs

| Port | Description |
|------|------------|
| `out` | Integrated output signal. |

---

## Notes

- The block has internal state.
- Direct feedthrough depends on the integration method:
  - no direct feedthrough for forward Euler,
  - direct feedthrough for backward Euler.
- The integrator uses a fixed-step discrete formulation.
- Input dimension changes between steps are not allowed.
- This block is equivalent to the Simulink **Discrete-Time Integrator** block.
- Policy:
    + Never propagate None: output is always a 2D array (at least (1,1)).
    + Shape is NOT frozen while we are in placeholder shape (1,1) and no explicit
      non-scalar initial_state was given.
    + As soon as a non-scalar input appears (shape != (1,1)), the shape becomes frozen.
    + If initial_state is provided and non-scalar, it freezes the shape immediately.
      If initial_state is scalar (1,1), it is treated as a placeholder: can be upgraded
      once a non-scalar input appears.
    + After shape is frozen, any non-scalar input shape mismatch raises ValueError.
    + If shape is frozen to (m,n), scalar input (1,1) is broadcast to (m,n).


---
© 2026 Université de Lille & INRIA – Licensed under LGPL-3.0-or-later
