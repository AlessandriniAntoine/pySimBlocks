# Glossary
```{glossary}
Algebraic loop
    A cycle in the direct-feedthrough dependency graph. If block A needs
    B's output to compute its own, and B needs A's output, neither can go
    first. pySimBlocks raises a `RuntimeError` at compile time when such
    a cycle is detected.
    See {doc}`execution_order`.

Block
    The fundamental unit of a pySimBlocks model. A block encapsulates a
    discrete-time computation and exposes a uniform interface — `initialize()`,
    `output_update()`, `state_update()` — called by the simulator at each step.

Direct feedthrough
    A block has direct feedthrough if its output at step `k` depends on
    its input at the same step `k` — i.e. `u[k]` appears in
    `output_update()`. This property determines which edges appear in the
    dependency graph and therefore the execution order.
    See {doc}`execution_order`.

Execution order
    The ordered list of blocks in which `output_update()` is called at
    each simulation step. Computed once during the compilation phase by
    a topological sort of the direct-feedthrough dependency graph.
    See {doc}`execution_order`.

Model
    A container that holds blocks and signal connections. The model builds
    the topological execution order and provides fast access to downstream
    connections. It is passed to the `Simulator` at construction time.
    See {py:class}`~pySimBlocks.core.model.Model`.

Port
    A named connection point on a block. Input ports receive signals from
    upstream blocks; output ports emit signals to downstream blocks.
    Ports are declared in `__init__` as entries in `self.inputs` and
    `self.outputs`.

Sample time
    The period in seconds at which a block is activated. Blocks with
    `sample_time=None` inherit the global `dt` from `SimulationConfig`.
    All sample times must be integer multiples of `dt`.

Signal
    A NumPy array of shape `(n, m)` flowing between two ports through a
    connection. All signals are discrete-time: a signal has a defined value
    at each simulation step `k`.

Simulator
    The central object that drives a pySimBlocks simulation. It takes a
    `Model` and a `SimulationConfig`, compiles the execution order, and
    runs the step loop until the end time is reached.
    See {doc}`simulation_lifecycle`.

State
    The internal memory of a block, split into two dicts: `state` holds
    the committed value `x[k]` used during `output_update()`, and
    `next_state` holds the value `x[k+1]` computed by `state_update()`
    before it is committed at the end of the step.

Task
    A group of blocks sharing the same sample time. The simulator groups
    blocks into tasks at compile time and activates each task only when
    its period has elapsed.
    See {doc}`simulation_lifecycle`.
```
