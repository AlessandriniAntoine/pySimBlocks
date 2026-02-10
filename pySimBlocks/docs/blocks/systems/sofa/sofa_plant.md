# SofaPlant

## Description

The **SofaPlant** block embeds a [SOFA](https://www.sofa-framework.org/) simulation as a dynamic system inside a pySimBlocks model.

Unlike *SofaExchangeIO*, which is used inside a SOFA controller, **SofaPlant runs the SOFA simulation itself** in a separate worker process and exposes it as a discrete-time plant.
However, this block can be used in a diagram that will be run in both simulations with pySimblocks as master and SOFA as master. In the second case, the block is automatically replaced by a *SofaExchangeIO* block.

At each simulation step:
- control inputs are sent to SOFA,
- the scene advances by one time increment,
- updated outputs are returned to pySimBlocks.

## Mathematical abstraction

The block can be seen as a discrete-time nonlinear system:

$$
y[k+1] = \mathcal{F}_{\text{SOFA}}(y[k], u[k])
$$

where:
- $ u[k] $ are the inputs defined by `input_keys`,
- $ y[k] $ are the outputs defined by `output_keys`,
- $ \mathcal{F}_{\text{SOFA}} $ represents one SOFA simulation step.

---

## Parameters

| Name | Type | Description | Required |
|------|------|-------------|----------|
| `scene_file` | string | Path to the SOFA scene file to be simulated. | Yes |
| `input_keys` | list[string] | Names of the input ports $ u_1, \dots, u_m $. | Yes |
| `output_keys` | list[string] | Names of the output ports returned by the output function. | Yes |
| `sample_time` | float | Execution period of the block. If omitted, the global simulation time step is used. | No | 

## Inputs

Inputs are dynamically defined by `input_keys`.  

- Each input must be connected.
- Each input is a NumPy array of shape (n, 1).
- Each input corresponds to a command sent to the SOFA controller.

## Outputs

Outputs are ynamically defined by `output_keys`.

- Each output is a NumPy array of shape (n, 1).
- Each output corresponds to a measurement extracted from the SOFA scene.

## Execution semantics

- The block has internal state.
- There is no direct feedthrough.
- One SOFA simulation step is executed per block activation.


---
© 2026 Université de Lille & INRIA – Licensed under LGPL-3.0-or-later
