# Developer Documentation - GUI Project Structure

## Architectural Overview

The system follows this seperation of responsibilities:
- ProjectState -> Owns the data model and acts as the source of truth.
- ProjectController -> Handles Logic and consistency.
- DiagramView -> Manages the user Interface?

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

[View the UML Diagram](uml/pySimBlocks-GUI.pdf)