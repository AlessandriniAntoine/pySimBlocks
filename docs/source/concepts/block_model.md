# Block Model

## Overview

A block is the fundamental unit of a pySimBlocks model. It encapsulates a
discrete-time computation — sources, operators, controllers, physical plants
— and exposes a uniform interface that the {doc}`simulator <simulation_lifecycle>`
calls at each step.

Every block inherits from {py:class}`~pySimBlocks.core.block.Block` and
implements at minimum `initialize()` and `output_update()`.

To add a new block to pySimBlocks — including its GUI metadata and index
registration — see {doc}`adding_block`.

## Anatomy of a block

### Inputs and outputs

Inputs and outputs are plain Python dicts mapping port names to NumPy arrays
of shape `(n, m)`. They are declared in `__init__` and updated each step.
```python
self.inputs["in"] = None      # declared, not yet connected
self.outputs["out"] = None    # declared, not yet computed
```

An input is `None` until a connection is established. An output is `None`
until `initialize()` or `output_update()` sets it. Accessing a `None` input
in `output_update()` should raise a `RuntimeError`.

### State

State is also a dict, split into two separate dicts: `state` holds the
current value `x[k]`, and `next_state` holds the value computed by
`state_update()` before it is committed.
```python
self.state["x"] = np.zeros((2, 1))
self.next_state["x"] = np.zeros((2, 1))
```

A block with no state simply leaves both dicts empty. The simulator checks
`block.has_state` to decide whether to call `state_update()` and
`commit_state()`.

### Parameters

Parameters are regular Python attributes set in `__init__`. There is no
dedicated container — a gain value, a matrix, a file path are all just
attributes.
```python
self.K = np.array(gain)
self.sample_time = sample_time
```

They are fixed at construction time and should not change during simulation.

## Block lifecycle methods

### initialize()

Called once before the simulation loop starts, in topological order.
Must set a valid initial value for all outputs and state entries.
Receives `t0`, the initial simulation time.
```python
def initialize(self, t0: float) -> None:
    self.state["x"] = np.zeros((2, 1))
    self.outputs["out"] = self.state["x"].copy()
```

### output_update()

Called every step for all active blocks, in topological order.
Must compute `outputs` from `state` and `inputs`. Must not modify `state`.
```python
def output_update(self, t: float, dt: float) -> None:
    self.outputs["out"] = self.state["x"].copy()
```

### state_update()

Called every step, after all `output_update()` calls. Must write the next
state into `next_state`. Must not modify `state` or `outputs`.
```python
def state_update(self, t: float, dt: float) -> None:
    self.next_state["x"] = self.state["x"] + dt * self.inputs["in"]
```

Only called if `block.has_state` is `True`. Blocks with no state can omit
this method.

### finalize()

Called once after the simulation loop ends. Optional — the base class
provides a no-op default. Use it to close files, release resources, or
flush buffers.

## direct_feedthrough flag

`direct_feedthrough` is a class-level boolean attribute that tells the
simulator whether `u[k]` appears in `output_update()`. It defaults to
`True` in the base class and should be overridden when the block's output
does not depend on its inputs at the same step.
```python
class MyIntegrator(Block):
    direct_feedthrough = False
```

Setting it correctly is critical — it determines which edges appear in the
dependency graph and therefore the execution order. An incorrect value either
causes unnecessary ordering constraints or, worse, silently produces stale
inputs. See {doc}`execution_order` for details.

