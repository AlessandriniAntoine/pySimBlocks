# WhiteNoise

## Summary

The **WhiteNoise** block generates independent Gaussian noise samples
for each output dimension at every simulation step.

---

## Mathematical definition

For each output component $i$, the signal is defined as:

$$
y_i(t) \sim \mathcal{N}(\mu_i, \sigma_i^2)
$$

where:
- $\mu_i$ is the mean,
- $\sigma_i$ is the standard deviation.

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `mean` | scalar or vector or matrix | Mean value of the noise. Scalars are broadcast to all dimensions. Default is zero. | True |
| `std` | scalar or vector or matrix | Standard deviation of the noise. Must be non-negative. Default is one. | True |
| `seed` | integer | Random seed for reproducibility. If provided, the noise sequence is deterministic. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

This block has **no inputs**.

---

## Outputs

| Port | Description |
|------|------------|
| `out` | Gaussian noise output signal. |

---

## Notes

- The block has no internal state.
- Noise samples are drawn independently at each simulation step.
- Each output dimension may have a different mean and standard deviation.
- Scalar parameters are automatically broadcast.
