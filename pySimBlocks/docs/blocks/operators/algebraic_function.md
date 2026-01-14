# Algebraic Function

## Summary

The **Algebraic Function** block evaluates a user-defined, stateless Python
function at each simulation step.

It implements an algebraic mapping between input and output signals, possibly
depending on the current simulation time.

---

## Mathematical definition

The block implements a general algebraic relation of the form:

$$
y[k] = g(t_k, \Delta t_k, u_1[k], u_2[k], \dots)
$$

where:
- $ u_i[k] $ are the input signals at step $k$,
- $ y[k] $ is the output signal,
- $ t_k $ is the current simulation time,
- $ \Delta t_k $ is the time step since the previous activation.

The function $ g $ is provided by the user as a Python function.

---

## Parameters

| Name | Type | Description | Required |
|------|------|-------------|----------|
| `file_path` | string | Path to the Python file containing the user-defined function. | Yes |
| `function_name` | string | Name of the function $ g $  to call inside the block. | Yes |
| `input_keys` | list[string] | Names of the input ports $ u_1, \dots, u_m $. | Yes |
| `output_keys` | list[string] | Names of the output ports returned by the output function. | Yes |
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

---

## Execution semantics

- The block is stateless.
- The block has direct feedthrough.
- At each activation, the function is evaluated as:

```python
g(t, dt, **inputs)
```
