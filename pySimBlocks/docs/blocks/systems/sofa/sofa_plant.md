# SofaPlant

## Description

The **SofaPlant** block embeds a [SOFA](https://www.sofa-framework.org/) simulation as a dynamic system inside a pySimBlocks model.

Unlike [`SofaExchangeIO`](./sofa_exchange_i_o.md), which is used inside a SOFA controller, **SofaPlant runs the SOFA simulation itself** in a separate worker process and exposes it as a discrete-time plant.

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

## Inputs and outputs

- **Inputs**  
  Dynamically defined by `input_keys`.  
  Each input corresponds to a command sent to the SOFA controller.

- **Outputs**  
  Dynamically defined by `output_keys`.  
  Each output corresponds to a measurement extracted from the SOFA scene.

## Execution semantics

- The block has internal state.
- There is no direct feedthrough.
- One SOFA simulation step is executed per block activation.

## Typical use cases

- Closed-loop control of soft robots simulated in SOFA
- Co-simulation between pySimBlocks controllers and SOFA physics
- Rapid prototyping of control laws on complex deformable systems
