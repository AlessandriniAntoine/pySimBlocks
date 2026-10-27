# TransferFunction

## Summary

The **TransferFunction** block implements a SISO transfer function, executed
internally as an equivalent discrete-time state-space system.

If `domain` is `discrete`, `num`/`den` are polynomials in $z$ and used
directly. If `domain` is `continuous`, `num`/`den` are polynomials in $s$
and the block is discretized **once**, at construction time, using
`sample_time` as the discretization period.

---

## Mathematical definition

$$
H(s) = \frac{\text{num}(s)}{\text{den}(s)} \quad \text{or} \quad
H(z) = \frac{\text{num}(z)}{\text{den}(z)}
$$

Realized as a companion-form state-space system and executed as:

$$
x[k+1] = A x[k] + B u[k]
$$

$$
y[k] = C x[k] + D u[k]
$$

where $A$, $B$, $C$, $D$ are the (discretized, if applicable) realization
actually simulated, not `num`/`den` themselves.

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `num` | 1D array | Numerator coefficients, decreasing powers. E.g. for $2s+3$: `[2, 3]`. | False |
| `den` | 1D array | Denominator coefficients, decreasing powers. E.g. for $s^2+4s+5$: `[1, 4, 5]`. Must not be identically zero; degree must be ≥ degree of `num`. | False |
| `domain` | enum (`continuous`, `discrete`) | Domain of `num`/`den`: polynomials in $s$ or in $z$. Default `discrete`. | True |
| `discretization` | enum (`tustin`, `zoh`) | Discretization method, used only when `domain` is `continuous`. `tustin` has no extra dependency; `zoh` requires `scipy`. Default `tustin`. | True |
| `x0` | 1D array | Initial state vector of size (n,). If omitted, the state is initialized to zero. | True |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used — including when `domain` is `continuous`, where it is then used as the discretization period. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `u` | Input signal. |

---

## Outputs

| Port | Description |
|------|------------|
| `x` | State vector of the realized state-space system. |
| `y` | Output signal. |

---

## Notes

- SISO only. For MIMO systems, use `LinearStateSpace` directly with `A/B/C/D`.
- The block has internal state.
- The realization is computed once at construction; the simulation loop
  itself always runs a discrete-time system, regardless of `domain`.
- Direct feedthrough is enabled automatically whenever the realized `D` is
  non-zero (e.g. a proper but non-strictly-proper transfer function, or a
  pure gain). As with `LinearStateSpace`, a `Delay` block is required to
  break an algebraic loop involving this block.
- With `domain="continuous"` and `discretization="tustin"`, the block is
  treated as having direct feedthrough even for a strictly proper transfer
  function (e.g. $1/s$), because Tustin generically introduces one. Use
  `discretization="zoh"` if you need to preserve strict properness.
- With `domain="continuous"`, the actual discretization is performed at
  `initialize()` time (once `sample_time`, explicit or global, is
  resolved) rather than at block creation.
- `discretization="zoh"` requires `scipy`; if it is not installed, the
  block raises a clear `ImportError` suggesting `tustin` instead.


---
© 2026 Université de Lille & INRIA – Licensed under LGPL-3.0-or-later
