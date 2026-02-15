# Demux

## Summary

The **Demux** block splits one input column vector into multiple output
column vectors.

---

## Mathematical definition

Given an input vector $\mathrm{in} \in \mathbb{R}^{n \times 1}$ and
$p$ outputs:

$$
q = \left\lfloor \frac{n}{p} \right\rfloor, \quad
m = n \bmod p
$$

The output segments are:
- the first $m$ outputs have size $(q+1, 1)$,
- the remaining $(p-m)$ outputs have size $(q, 1)$.

This corresponds to an even split with the remainder distributed on the
first outputs.

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `num_outputs` | integer | Number of output ports to create. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `in` | Input column vector of shape $(n,1)$. |

---

## Outputs

| Port | Description |
|------|------------|
| `out1 … outP` | Output vector segments according to the split rule above. |

---

## Notes

- The block has no internal state.
- The block has direct feedthrough.
- Input must be a column vector of shape $(n,1)$.
- The parameter `num_outputs` must satisfy $1 \le p \le n$.
- This block is equivalent to the Simulink **Demux** concept for vector splitting.


---
© 2026 Université de Lille & INRIA – Licensed under LGPL-3.0-or-later
