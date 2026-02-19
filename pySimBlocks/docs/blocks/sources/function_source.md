# FunctionSource

## Summary

The **FunctionSource** block generates one or more signals from a user-defined Python function
without any input ports.

At each activation, it evaluates:

$$
y[k] = f(t_k, \Delta t_k)
$$

where $t_k$ is the current simulation time and $\Delta t_k$ is the elapsed time
since the previous activation.

---

## Parameters

| Name | Type | Description | Required |
|------|------|-------------|----------|
| `file_path` | string | Path to the Python file containing `f`. | Yes |
| `function_name` | string | Name of the function to call inside the file. | Yes |
| `output_keys` | list[string] | Names of the output ports. The function must return a dict with exactly these keys. | Yes |
| `sample_time` | float | Execution period of the block. If omitted, the global simulation time step is used. | No |

---

## Inputs

This block has **no inputs**.

---

## Outputs

Outputs are dynamically defined by `output_keys`.

---

## Execution semantics

- The function signature must be exactly: `f(t, dt)`.
- The function must return a dict with keys exactly matching `output_keys`.
- Each returned value may be scalar, 1D, or 2D and is normalized to a 2D array.
- Output shape is frozen per output key after first evaluation and must stay constant.
- The block is stateless.


---
© 2026 Université de Lille & INRIA – Licensed under LGPL-3.0-or-later
