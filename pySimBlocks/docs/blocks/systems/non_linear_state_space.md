# Non Linear State Space

## Summary

The **NonLinearStateSpace** block represents a user-defined, discrete-time non linear
state-space system.

The system dynamics and outputs are defined by Python functions provided by the user,
while the block itself enforces a strict execution and data-flow contract compatible
with the pySimBlocks simulation semantics.

---

## Mathematical definition

The block represents a discrete-time system of the form:

$$
\begin{aligned}
x[k+1] &= f\bigl(t_k,\ \Delta t_k,\ x[k],\ u_1[k],\dots,u_m[k]\bigr) \\
y[k]   &= g\bigl(t_k,\ \Delta t_k,\ x[k]\bigr)
\end{aligned}
$$

where:
- $ x[k] \in \mathbb{R}^n $ is the state vector,
- $ u_i[k] $ are the input signals,
- $ y[k] $ is the output signal,
- $ t_k $ is the current simulation time,
- $ \Delta t_k $ is the elapsed time since the previous activation.

The functions $ f $ and $ g $ are implemented by the user and executed at each
block activation.

---

## Parameters

| Name | Type | Description | Required |
|------|------|-------------|----------|
| `file_path` | string | Path to the Python file containing the user-defined functions. | Yes |
| `state_function_name` | string | Name of the state update function implementing $ f $. | Yes |
| `output_function_name` | string | Name of the output function implementing  $ g $. | Yes |
| `input_keys` | list[string] | Names of the input ports $ u_1, \dots, u_m $. | Yes |
| `output_keys` | list[string] | Names of the output ports returned by the output function. | Yes |
| `x0` | vector | Initial state vector \(x[0]\). | Yes |
| `sample_time` | float | Execution period of the block. If omitted, the global simulation time step is used. | No | 

--- 

## Inputs 

Inputs are dynamically defined by `input_keys`. 

- Each input must be connected. 
- Each input is a NumPy array of shape $ (n,1) $. 

--- 

## Outputs 

Outputs are dynamically defined by `output_keys`. 

- Each output is a NumPy array of shape $ (n,1) $. 
- Outputs depend only on the current state (no direct feedthrough). 

--- 

## Execution semantics

- The block **has internal state**.
- The block **has no direct feedthrough**.
- Execution follows the standard two-phase discrete-time semantics:
  1. Outputs are computed from the current state.
  2. The next state is computed from the current state and current inputs.

---

## Notes

- This block provides a generic interface for embedding non linear models into a
  block-diagram simulation.
- The numerical stability and correctness of the system are the responsibility of
  the user-defined functions.
- Advanced users may instantiate this block directly from Python using callable
  functions instead of file-based definitions.
