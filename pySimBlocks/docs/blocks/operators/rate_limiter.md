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

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `rising_slope` | scalar or vector | Maximum allowed positive rate of change. Default is no positive rate limit. | True |
| `falling_slope` | scalar or vector | Maximum allowed negative rate of change. Default is no negative rate limit. | True |
| `initial_output` | scalar or vector | | Initial output value used as $y[-1]$. If not provided, the initial output is set equal to the first input. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `in` | Input signal. |

---

## Outputs

| Port | Description |
|------|------------|
| `out` | Rate-limited output signal. |

---

## Notes

- The block has internal state.
- The block has direct feedthrough.
- Rate limits are applied component-wise.
- Scalar parameters are automatically broadcast.
- Absence of a rate limit in one direction is represented by an infinite slope.
- This block is equivalent to the Simulink **Rate Limiter** block.
