# PolytopicStateSpace

## Summary

The **PolytopicStateSpace** block implements a discrete-time polytopic state-space model without direct feedthrough.

---

## Mathematical definition

The system is defined by:

$$
x[k+1] = \sum_{i=1}^{r} w_i[k] (A_i x[k] + B_i u[k])
$$

$$
y[k] = C x[k]
$$

where:
- $x[k] \in \mathbb{R}^{nx}$ is the state vector,
- $u[k] \in \mathbb{R}^{nu}$ is the input vector,
- $w[k] \in \mathbb{R}^{r}$ is the vertex weight vector,
- $y[k] \in \mathbb{R}^{ny}$ is the output vector.

The block expects:
- $A \in \mathbb{R}^{nx \times (r\,nx)}$ as $[A_1 \ \cdots \ A_r]$,
- $B \in \mathbb{R}^{nx \times (r\,nu)}$ as $[B_1 \ \cdots \ B_r]$,
- $C \in \mathbb{R}^{ny \times nx}$.

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `A` | 2D array | Stacked state matrix of size (nx, r*nx): `[A1, ..., Ar]`. | False |
| `B` | 2D array | Stacked input matrix of size (nx, r*nu): `[B1, ..., Br]`. | False |
| `C` | 2D array | Output matrix of size (ny, nx). | False |
| `x0` | 1D array | Initial state vector of size (nx,). If omitted, initialized to zero. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `w` | Weight vector of shape (r,1) (or `(r,)` as parameterized array). |
| `u` | Input vector of shape (nu,1). |

---

## Outputs

| Port | Description |
|------|------------|
| `x` | State vector of shape (nx,1). |
| `y` | Output vector of shape (ny,1). |

---

## Notes

- The block has internal state.
- The system is strictly proper (no direct feedthrough).
- Input dimensions are validated at runtime.


---
© 2026 Université de Lille & INRIA – Licensed under LGPL-3.0-or-later
