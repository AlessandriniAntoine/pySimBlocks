# Gain Block

## Description

The **Gain** block applies a static transformation to its input signal using a gain **K**.

Depending on the selected multiplication mode, it computes one of:

- **Element-wise**:  
  $$ y = K \odot u $$
- **Left matrix product**:  
  $$ y = K \cdot u $$
- **Right matrix product**:  
  $$ y = u \cdot K $$

Where:
- $u$ is the input signal (2D array),
- $K$ is the gain,
- $y$ is the output signal.

---

## Multiplication modes

### 1) Element wise (K * u)

Element-wise multiplication with strict shape rules (no implicit matrix product):

- **K scalar**: `y = K * u`  
  Works for any 2D `u` shape `(m,n)`.

- **K vector (m,)**: `y = K[:,None] * u`  
  Requires `u.shape[0] == m`. Output shape is `(m,n)`.

- **K matrix (m,n)**: `y = K * u`  
  Requires `u.shape == (m,n)`.

Any other mismatch raises an error.

---

### 2) Matrix (K @ u)

Left matrix product:

- Requires **K is a 2D matrix** with shape `(p,m)`
- Requires input `u` is 2D with shape `(m,ncols)`
- Output `y` has shape `(p,ncols)`

---

### 3) Matrix (u @ K)

Right matrix product:

- Requires **K is a 2D matrix** with shape `(m,q)`
- Requires input `u` is 2D with shape `(nrows,m)`
- Output `y` has shape `(nrows,q)`

---

## Parameters

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `gain` | scalar, vector (m,), or matrix (p,m) / (m,q) | Gain coefficient(s). | False |
| `multiplication` | string enum | `"Element wise (K * u)"` \| `"Matrix (K @ u)"` \| `"Matrix (u @ K)"` | True (default: element-wise) |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `in` | Input signal $u$ (**must be a 2D NumPy array**). |

---

## Outputs

| Port | Description |
|------|------------|
| `out` | Output signal $y$ (2D array). |

---

## Notes

- The Gain block is **stateless** and **direct feedthrough**.
- Inputs must be **2D** (`ndim == 2`). No implicit reshape/flatten is applied.
- Dimension mismatches raise an error.
- This block is conceptually similar to Simulink **Gain**, but the multiplication behavior is made explicit via `multiplication`.
