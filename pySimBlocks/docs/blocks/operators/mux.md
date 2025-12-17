# Mux

## Summary

The **Mux** block concatenates multiple input column vectors vertically
into a single output column vector.

---

## Mathematical definition

Given $N$ input vectors $\mathrm{in}_i \in \mathbb{R}^{n_i \times 1}$,
the output is defined as:

$$
\mathrm{out} =
\begin{bmatrix}
\mathrm{in}_1 \\
\mathrm{in}_2 \\
\vdots \\
\mathrm{in}_N
\end{bmatrix}
$$

The resulting output dimension is $(\sum_i n_i, 1)$.

---

## Parameters

### `num_inputs` (optional)

Number of input ports to create.

- Must be a positive integer
- Default value is 2

### `sample_time` (optional)

Execution period of the block.

If not specified, the simulator time step is used.

---

## Inputs

### `in1 … inN`

Input column vectors.

- Dynamically defined by `num_inputs`
- Each input must have shape $(n_i, 1)$

---

## Outputs

### `out`

Vertically concatenated output vector.

- Dimension: $(\sum_i n_i, 1)$

---

## Notes

- The block has no internal state.
- The block has direct feedthrough.
- Input vectors are not required to have the same dimension.
- All input ports must be connected for the block to produce an output.
- This block is equivalent to the Simulink **Mux** block.
