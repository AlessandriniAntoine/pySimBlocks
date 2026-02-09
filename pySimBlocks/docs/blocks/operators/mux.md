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

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `num_inputs` | integer | Number of input ports to create. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `in1 … inN` | Input column vectors to be concatenated. |

---

## Outputs

| Port | Description |
|------|------------|
| `out` | Vertically concatenated output vector. |

---

## Notes

- The block has no internal state.
- The block has direct feedthrough.
- Input vectors are not required to have the same dimension.
- All input ports must be connected for the block to produce an output.
- This block is equivalent to the Simulink **Mux** block.


---
© 2026 Université de Lille & INRIA – Licensed under LGPL-3.0-or-later
