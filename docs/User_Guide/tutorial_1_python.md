# Tutorial 1: First Steps with pySimBlocks

## 1. Overview

### 1.1 Goals 

This example introduces the core concepts of pySimBlocks: 
-  Creating blocks 
- Connecting signals 
- Running a discrete-time simulation 
- Logging and plotting results 

By the end of this tutorial, you will be able to build and simulate your own block-based model in Python.

### 1.2 System Description

We build a simple closed-loop control system composed of three elements: 
- a step reference, 
- a PI controller, 
- a first-order discrete-time linear plant.

![Block-Diagram](./images/tutorial_1-block_diagram.png)

**Plant — Linear State-Space System**  
The plant is a discrete-time first-order linear system defined by:
$$\begin{array}{rcl} x[k+1] &=& a\,x[k] + b\,u[k] \\ y[k] &=& x[k] \end{array}$$
The initial state is $x[0] = 0$.

**Controller — PI**  
The PI controller computes a control command from the tracking error $e[k] = r[k] - y[k]$:
$$ u[k] = K_p\, e[k] + x_i[k] $$
where the integral state evolves as:
$$x_i[k+1] = x_i[k] + K_i\, e[k]\, dt$$
The integral action ensures zero steady-state error on a step reference. 

## 2. Complete Example

Below is the full working example.  
You can find it in the file
[main.py](../../examples/tutorials/tutorial_1_python/main.py) in the repository.

```python
import matplotlib.pyplot as plt
import numpy as np

from pySimBlocks import Model, SimulationConfig, Simulator
from pySimBlocks.blocks.controllers import Pid
from pySimBlocks.blocks.operators import Sum
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import LinearStateSpace


def main():
    """This example demonstrates how to use the pySimBlocks library to create a 
    simple closed-loop control system with a step reference input, a PI controller, 
    and a linear state-space system.
    """

    A = np.array([[0.9]])
    B = np.array([[0.5]])
    C = np.array([[1.0]])
    x0 = np.zeros((A.shape[0], 1))

    Kp = np.array([[0.5]])
    Ki = np.array([[2.]])

    # -------------------------------------------------------
    # 1. Create the blocks
    # -------------------------------------------------------
    step = Step(
        name="ref",
        value_before=np.array([[0.0]]),
        value_after=np.array([[1.0]]),
        start_time=0.5
    )
    sum = Sum(name="error", signs="+-")
    pid = Pid(name="pid", controller="PI", Kp=Kp, Ki=Ki)
    system = LinearStateSpace(name="system", A=A, B=B, C=C, x0=x0)

    # -------------------------------------------------------
    # 2. Build the model
    # -------------------------------------------------------
    model = Model("test")
    for block in [step, sum, pid, system]:
        model.add_block(block)

    model.connect("ref", "out", "error", "in1")
    model.connect("system", "y", "error", "in2")
    model.connect("error", "out", "pid", "e")
    model.connect("pid", "u", "system", "u")

    # -------------------------------------------------------
    # 3. Create the simulator
    # -------------------------------------------------------
    dt = 0.01 # seconds
    T = 5. # seconds
    sim_cfg = SimulationConfig(dt, T)
    sim = Simulator(model, sim_cfg, verbose=False)

    # -------------------------------------------------------
    # 4. Run the simulation with logging
    # -------------------------------------------------------
    logs = sim.run(logging=[
            "ref.outputs.out",
            "pid.outputs.u",
            "system.outputs.y"
        ]
    )

    # -------------------------------------------------------
    # 5. Extract logged data
    # -------------------------------------------------------
    t = sim.get_data("time")
    u = sim.get_data("pid.outputs.u").squeeze()
    r = sim.get_data("ref.outputs.out").squeeze()
    y = sim.get_data("system.outputs.y").squeeze()

    # -------------------------------------------------------
    # 6. Plot the result
    # -------------------------------------------------------
    fig, axs = plt.subplots(1, 2, sharex=True)
    axs[0].step(t, r, "--r", label="ref", where="post")
    axs[0].step(t, y, "--b", label="output", where="post")
    axs[0].set_xlabel("Time [s]")
    axs[0].set_ylabel("Amplitude")
    axs[0].set_title("Closed-loop response")
    axs[0].grid(True)
    axs[0].legend()

    axs[1].step(t, u, "--b", label="u[k] (pid output)", where="post")
    axs[1].set_xlabel("Time [s]")
    axs[1].set_ylabel("Amplitude")
    axs[1].set_title("PID controller output")
    axs[1].grid(True)
    axs[1].legend()

    plt.show()

```
## 3. How It Works

The example follows a simple workflow:

1. **Blocks are created**  
   Each component of the system (reference, controller, plant) is represented as a block.
2. **Blocks are added to a Model**  
   The `Model` acts as a container for all blocks.
3. **Signals are connected explicitly**  
   Connections define how outputs are propagated to downstream inputs, forming a directed graph.
4. **The Simulator executes the model in discrete time**  
   At each time step:
   - Blocks compute their outputs
   - Signals are propagated
   - States are updated
5. **Selected signals are logged and retrieved**  
   Logged variables can be accessed using `sim.get_data()` and visualized with standard Python tools.

This structure reflects the core philosophy of pySimBlocks: explicit block modeling with deterministic discrete-time execution.

## 4. About the data shapes

All signals in pySimBlocks follow a strict 2D convention:

- Scalars are represented as `(1,1)`
- Vectors are `(n,1)`
- Matrices are `(m,n)`

When logging a SISO signal over time, the resulting array has shape: `(N, 1, 1)` where `N` is the number of simulation steps.

For plotting convenience, we use:
```python
y = sim.get_data("system.outputs.y").squeeze()
```

## 5. Try it yourself

To better understand the framework, try experimenting with:

- Changing the controller gains (`Kp`, `Ki`)
- Modifying the system dynamics (`A`, `B`)
- Adjusting the time step `dt`
- Increasing the simulation duration `T`

Observe how the closed-loop response changes.

This simple example is the foundation for more advanced use cases,
including:
- [GUI modeling](./tutorial_2_gui.md), 
- [SOFA integration](./tutorial_3_sofa.md), 
- Hardware implementation.

