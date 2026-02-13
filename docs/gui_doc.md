# Developer Documentation - GUI Project Structure

[View the UML Diagram](uml/pySimBlocks-GUI.pdf)

## Architectural Overview

The system follows this seperation of responsibilities:
- ProjectState -> Owns the data model and acts as the source of truth.
- ProjectController -> Handles Logic and consistency.
- DiagramView -> Manages the user Interface.

# Model vs View Representation

## Conceptual Separation

The architecture relies on a strict distinction between:

- **`...Instance` classes -> Model Layer**
- **`...Item` classes -> View Layer**

## `...Instance` classes -> Model Representation

### Role

Classes suffixed with **`Instance`** represent the **logical structure of the diagram**.

They are:
- UI-independent
- Serializable
- Used by the simulation core
- The source of truth

### Responsabilities

`Instance` objects encapsulate:

- Structural data
- Simulation parameters
- Business rules

Examples:

- `BlockInstance`
- `PortInstance`
- `ConnectionInstance`

### Simulation Interaction

Only `Instance` objects are passed to the simulation engine:

## `...Item` classes -> View Representation

### Role

Classes suffixed with **`Item`** represent **visial elements in the diagram scene**.

They are:
- UI-only
- Responsible for rendering
- Responsible for interaction
- Never used by the simulation core

### Responsibilities

`*Item` objects handle:

- Drawing
- Mouse interactions
- Visual updates
- Scene management

Examples:

- `BlockItem`
- `PortItem`
- `ConnectionItem`

### Relationship with Instances

Each visual item references its corresponding model instance:
- BlockItem -> BlockInstance
- PortItem -> PortInstance
- ConnectionItem -> ConnectionInstance


## Synchronization Strategy

All updates follow this flow:
1. User Interation
2. DiagramView Event (Item)
3. Call ProjectController API
4. Update ProjectState (Instance)
5. Update DiagramView (Item)

---

# Block Metadata System

The GUI relies on a dynamic block registry that automatically discovers available blocks at runtime.
Instead of hardcoding imports, the system:
- Scans the filesystem
- imports metadata modules
- Instanciates BlockMeta subclasses
- Builds a structured registry 

This design allows blocks to be added without modifying core GUI code.

## Registry Structure

``` py
BlockRegistry = Dict[str, Dict[str, BlockMeta]]

{
    category_name_1: {
        block_type_a: BlockMeta
        block_type_B: BlockMeta
    },

    category_name_2: {
        block_type_c: BlockMeta
    }
}
```

Example:
``` json
{
    "controllers": {
        "PID": BlockMeta,
        "StateFeedback": BlocMeta,
    },

    "Operators": {
        "Sum": BlockMeta,
        "Gain": BlockMeta,
        ...
    }
    ...
}
```

## Resolve Mechanism

``` py
load_block_registry()
```
Responsible for building the registry.
1. Resolve metadata root directory
2. Recursively scan for `*.py` files
3. Import each module
4. Register all and only `BlockMeta` subclasses
5. Resolve documentation path associated with each block

This method assumes the following layout:
```
project_root/
│
├── gui/
│   └── blocks/
│       └── <category>/
│           └── <block_meta>.py
│
└── docs/
    └── blocks/
        └── <category>/
            └── <block_meta>.md   (optional)
```

## Add a new block to the GUI

This section explains how to add a new block to the GUI system by creating its metadata and optional documentation.
*(Assuming that your block exists in the core simulation engine)*

### Create a `BlockMeta` subclass

1. Create a new Python file for your block metadata:
```
gui/blocks/<my_block_category>/<my_block_meta>.py
```

2. Define your block by subclassing `BlockMeta`:
``` python
from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta

class MyBlockMeta(BlockMeta):

    def __init__(self):
        self.name = ""
        self.category = ""
        self.type = ""
        self.summary = ""
        self.description = (
            ""
        )

        self.parameters = [
            ParameterMeta(
                name="",
                type=""
            ),
        ]

        self.inputs = [
            PortMeta(
                name="",
                display_as=""
                shape=...
            ),
        ]

        self.outputs = [
            PortMeta(
                name="",
                display_as=""
                shape=...
            ),
        ]
```

**Tips**:
- "category" should match the folder structure
- "type" must be unique within the category

### (Optional) Add documentation

1. Create a Markdown file with the same name as your block meta:
```
docs/blocks/<my_block_category>/<my_block_meta>.md
```

2. Write documentation describing the block and its parameters.

### (Optional) Your block parameters depend on one another
Sometimes, the value or visibility of one parameter depends on the value of another. To handle this, override the `is_parameter_active` method in your `BlockMeta` subclass.

Example (based on pid):
``` python
def is_parameter_active(self, param_name: str, instance_values: Dict[str, Any]) -> bool:
    if param_name == "Kp":
        return instance_values["controller"] in ["P", "PI", "PD", "PID"]
    elif param_name == "Ki":
        return instance_values["controller"] in ["I", "PI", "PID"]
    elif param_name == "Kd":
        return instance_values["controller"] in ["PD", "PID"]
    return super().is_parameter_active(param_name, instance_values)
```
Explanation:
- `instance_values` contains the current values of all parameters for this block instance.
- The `controller` parameter determines which other parameters are active:
    - if the controller type includes `P`, then `Kp` is active.
    - if it includes `I`, then `Ki` is active.
    - if it includes `D`, then `Kd` is active.
- This mechanism ensures the GUI only shows relevant parameters for the selected controller type, reducing clutter and preventing invalid configurations.

### (Optional) Your block ports are dynamic
Some blocks need a variable number of input or output ports depending on parameter values. Override the `resolve_port_group` method in your `lockMeta` subclass to generate dynamic ports.

Example (based on sum):
``` python
def resolve_port_group(self, port_meta: PortMeta, direction: str, instance: "BlockInstance") -> list["PortInstance"]:
    if direction == "input" and port_meta.name == "in":
        signs = instance.parameters.get("signs", "")
        ports = []

        for i, sign in enumerate(signs):
            ports.append(
                PortInstance(
                    name=f"{port_meta.name}{i + 1}",
                    display_as=sign,
                    direction="input",
                    block=instance
                )
            )
        return ports
    
    return super().resolve_port_group(port_meta, direction, instance)
```
Explanation:
- `instance.parameters` provides the current values for this block instance.
- The `signs` parameter is a string where each character represents an input port (`+` or `-`).
    - Examples: "+++--" -> 3 inputs ports with `+` and 2 with `-`.
- The method generates a `PortInstance` for each character in the string, naming them uniquely (`in1`, `in2`, ...) and displaying the correct symbol.
- This allows the GUI to handle blocks with a flexible number of inputs or outputs depending on the block configurations.
