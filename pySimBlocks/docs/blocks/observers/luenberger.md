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

### `A`

System state matrix.

### `B`

Input matrix.

### `C`

Output matrix.

### `L`

Observer gain matrix.

### `x0` (optional)

Initial estimated state.

If not provided, the estimate is initialized to zero.

### `sample_time` (optional)

Execution period of the block.

If not specified, the simulator time step is used.

---

## Inputs

### `u`

Control input.

- Dimension: $(m, 1)$

### `y`

Measured output.

- Dimension: $(p, 1)$

---

## Outputs

### `x_hat`

Estimated state.

- Dimension: $(n, 1)$

### `y_hat`

Estimated output.

- Dimension: $(p, 1)$

---

## Notes

- The block has internal state.
- The observer has no direct feedthrough.
- Matrix $D$ is intentionally not supported to avoid algebraic loops.
- The state estimate is updated once per simulation step.
