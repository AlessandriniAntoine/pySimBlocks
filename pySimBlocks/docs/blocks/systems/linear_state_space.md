# LinearStateSpace

## Summary

The **LinearStateSpace** block implements a discrete-time linear state-space
system without direct feedthrough.

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

### `A`

State transition matrix.

### `B`

Input matrix.

### `C`

Output matrix.

### `x0` (optional)

Initial state vector.

If not provided, the state is initialized to zero.

### `sample_time` (optional)

Execution period of the block.

If not specified, the simulator time step is used.

---

## Inputs

### `u`

Input vector.

- Dimension: $(m, 1)$

---

## Outputs

### `x`

State vector.

- Dimension: $(n, 1)$

### `y`

Output vector.

- Dimension: $(p, 1)$

---

## Notes

- The block has internal state.
- The system is strictly proper (no direct feedthrough).
- Matrix $D$ is intentionally not supported to avoid algebraic loops.
- The output is computed from the current state.
