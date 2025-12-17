# DiscreteIntegrator

## Summary

The **DiscreteIntegrator** block integrates an input signal over time using
a discrete-time numerical integration scheme.

---

## Mathematical definition

The integrator state evolves according to:

$$
x[k+1] = x[k] + dt \, u[k]
$$

The output depends on the selected integration method.

### Euler forward

$$
y[k] = x[k]
$$

### Euler backward

$$
y[k] = x[k] + dt \, u[k]
$$

where:
- $u[k]$ is the input signal,
- $x[k]$ is the internal integrated state,
- $dt$ is the simulation time step.

---

## Parameters

### `initial_state` (optional)

Initial value of the integrated state.

- Scalar or vector-valued
- If not provided, the state is initialized lazily using a zero vector with
  dimension inferred from the first input

### `method` (optional)

Numerical integration method.

- `euler forward`
- `euler backward`
- Default value is `euler forward`

### `sample_time` (optional)

Execution period of the block.

If not specified, the simulator time step is used.

---

## Inputs

### `in`

Signal to integrate.

- Dimension: $(n, 1)$

---

## Outputs

### `out`

Integrated output signal.

- Dimension: $(n, 1)$

---

## Notes

- The block has internal state.
- Direct feedthrough depends on the integration method:
  - no direct feedthrough for forward Euler,
  - direct feedthrough for backward Euler.
- The integrator uses a fixed-step discrete formulation.
- Input dimension changes between steps are not allowed.
- This block is equivalent to the Simulink **Discrete-Time Integrator** block.
