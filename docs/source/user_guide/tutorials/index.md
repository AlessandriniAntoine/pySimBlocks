# Tutorials

This section provides a progressive learning path for `pySimBlocks`.

The tutorials are meant to be read in order. Each one builds on the previous
one and introduces a new way of working with the library.

```{toctree}
:maxdepth: 1

tutorial_1_python
tutorial_2_gui
tutorial_3_sofa
```

## Tutorial 1: First Simulation in Python

Prerequisites: a working `pySimBlocks` Python installation.
Level: Beginner.

Build and simulate a simple closed-loop system directly in Python.

You will learn:

- How to create blocks
- How to connect signals
- How to run a discrete-time simulation
- How to log and visualize results

After this tutorial, you will be able to assemble and simulate a basic model
from code.

## Tutorial 2: Build the Same Model with the GUI

Prerequisites: Tutorial 1 completed and the graphical editor available.
Level: Beginner.

Rebuild the same closed-loop system visually with the `pySimBlocks` GUI.

You will learn:

- How to add blocks in the editor
- How to configure block and simulation parameters
- How to connect signals visually
- How to save and export a GUI project

After this tutorial, you will be able to create the same model either from
code or from the graphical editor.

## Tutorial 3: Couple the Model with SOFA

Prerequisites: Tutorial 2 completed, SOFA installed, and the SOFA Python
bindings configured.
Level: Intermediate.

Replace the simple linear plant with a SOFA simulation and run the closed-loop
diagram in co-simulation.

You will learn:

- How to configure `SOFA_ROOT` and the SOFA Python bindings
- How to define a `SofaPysimBlocksController`
- How to configure a `SofaPlant` block in the GUI
- How to run the model with either `pySimBlocks` or SOFA as the master process

After this tutorial, you will be able to connect a `pySimBlocks` controller to
a SOFA scene and run the coupled system from the GUI or the published example
files.
