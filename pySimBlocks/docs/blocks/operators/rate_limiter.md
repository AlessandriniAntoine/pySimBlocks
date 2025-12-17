# RateLimiter

## Summary

The **RateLimiter** block limits the rate of change of its output signal by
constraining how fast the output can increase or decrease between successive
time steps.

---

## Mathematical definition

The rate-limited output is computed as:

$$
\Delta u = u[k] - y[k-1]
$$

$$
y[k] = y[k-1] + \mathrm{clip}(\Delta u,\; s^{-} dt,\; s^{+} dt)
$$

where:
- $u[k]$ is the current input,
- $y[k-1]$ is the previous output,
- $s^{+}$ is the rising slope (maximum positive rate),
- $s^{-}$ is the falling slope (maximum negative rate),
- $dt$ is the simulation time step.

---

## Parameters

### `rising_slope` (optional)

Maximum allowed positive rate of change.

- Scalar or vector-valued
- Must be greater than or equal to zero
- Default behavior corresponds to no positive rate limit

### `falling_slope` (optional)

Maximum allowed negative rate of change.

- Scalar or vector-valued
- Must be less than or equal to zero
- Default behavior corresponds to no negative rate limit

### `initial_output` (optional)

Initial output value used as $y[-1]$.

- Scalar or vector-valued
- If not provided, the initial output is set equal to the first input

### `sample_time` (optional)

Execution period of the block.

If not specified, the simulator time step is used.

---

## Inputs

### `in`

Input signal.

- Dimension: $(n, 1)$

---

## Outputs

### `out`

Rate-limited output signal.

- Dimension: $(n, 1)$

---

## Notes

- The block has internal state.
- The block has direct feedthrough.
- Rate limits are applied component-wise.
- Scalar parameters are automatically broadcast.
- Absence of a rate limit in one direction is represented by an infinite slope.
- This block is equivalent to the Simulink **Rate Limiter** block.
