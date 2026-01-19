# QuadraticProgram Block

## Description

The **QuadraticProgram** block solves a quadratic optimization problem at each simulation step.

It computes the solution of the following quadratic program:

$$
\begin{aligned}
\min_x \quad & \tfrac12 x^T P x + q^T x \\
\text{subject to} \quad
& Gx \le h \\
& Ax = b \\
& \ell \le x \le u
\end{aligned}
$$

where:
- $x$ is the decision variable,
- $P$ is the quadratic cost matrix,
- $q$ is the linear cost vector,
- $G, h$ define inequality constraints,
- $A, b$ define equality constraints,
- $\ell, u$ define lower and upper bounds.

All problem data are provided as inputs and may vary with time.

---

## Problem definition

The quadratic program solved by this block is fully time-varying:

- The cost function $(P, q)$ may change at each simulation step.
- Constraints $(G, h)$, $(A, b)$, and bounds $(\ell, u)$ are optional.
- If a constraint set is omitted, it is not enforced.

This block is suitable for:
- constrained control laws (e.g. saturated LQR),
- control allocation,
- one-step MPC formulations,
- projection-based controllers.

---

## Parameters

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `size` | int | Number of decision variables of the quadratic program. | False |
| `solver` | string | QP solver used internally via `qpsolvers` (e.g. `clarabel`). | True |

---

## Inputs

| Port | Description |
|------|------------|
| `P` | Quadratic cost matrix $(n \times n)$. Must be square and compatible with `size`. |
| `q` | Linear cost vector. Accepted shapes: $(n,)$ or $(n,1)$. |
| `G` | Inequality constraint matrix $(m \times n)$. Must be provided together with `h`. |
| `h` | Inequality constraint vector. Accepted shapes: $(m,)$ or $(m,1)$. |
| `A` | Equality constraint matrix $(p \times n)$. Must be provided together with `b`. |
| `b` | Equality constraint vector. Accepted shapes: $(p,)$ or $(p,1)$. |
| `lb` | Lower bound on decision variables. Accepted shapes: $(n,)$ or $(n,1)$. |
| `ub` | Upper bound on decision variables. Accepted shapes: $(n,)$ or $(n,1)$. |

---

## Outputs

| Port | Description |
|------|------------|
| `x` | Optimal solution of the quadratic program $(n \times 1)$. |
| `status` | Solver status code:<br>• `0`: optimal solution found<br>• `1`: problem infeasible<br>• `2`: solver or numerical error |
| `cost` | Optimal value of the quadratic cost function. |

---

## Execution semantics

- The block is **direct feedthrough**: outputs depend only on current inputs.
- The block is **stateless**: no internal dynamics or memory are stored.
- A new quadratic program is solved at each simulation step.

---

## Notes

- All dimension checks are performed before calling the solver.
- If the problem is infeasible or the solver fails, the output `status` reflects the error and the output vector is safely set to zero.
- This block relies on the `qpsolvers` Python package for numerical optimization.
- This block is conceptually similar to optimization blocks used in Simulink-based MPC and constrained control designs.
