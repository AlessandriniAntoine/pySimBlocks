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

### `mean` (optional)

Mean value of the noise.

- Scalar or vector-valued
- Scalars are broadcast to all dimensions
- Default value is zero

### `std` (optional)

Standard deviation of the noise.

- Scalar or vector-valued
- Must be non-negative
- Default value is one

### `seed` (optional)

Random seed for reproducibility.

If provided, the noise sequence is deterministic.

### `sample_time` (optional)

Execution period of the block.

If not specified, the simulator time step is used.

---

## Inputs

This block has **no inputs**.

---

## Outputs

### `out`

Gaussian noise output signal.

- Dimension: $(n, 1)$

---

## Notes

- The block has no internal state.
- Noise samples are drawn independently at each simulation step.
- Each output dimension may have a different mean and standard deviation.
- Scalar parameters are automatically broadcast.
