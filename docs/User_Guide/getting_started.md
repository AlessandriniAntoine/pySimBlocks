# Getting Started with pySimBlocks

pySimBlocks is a block-based simulation framework for control systems, 
supporting both programmatic and graphical modeling workflows.

This guide walks you through the core concepts in a progressive manner.
Recommended order: Tutorial 1 -> Tutorial 2 -> Tutorial 3.

## 1. First Simulation (Python)

Prerequisites: Python environment configured for pySimBlocks.
Level: Beginner.

Build and simulate a closed-loop system directly in Python.

You will learn:
- How to create blocks
- How to connect signals
- How to run a discrete-time simulation
- How to log and visualize results

→ [Start Tutorial 1 — Python API](tutorial_1_python.md)
After this tutorial: You can build and run a basic closed-loop model from code.

## 2. First Simulation (GUI)

Prerequisites: Tutorial 1 completed, pySimBlocks GUI installed.
Level: Beginner.

Rebuild the same system using the graphical interface.

You will learn:
- How to create a model visually
- How to configure blocks and simulation settings
- How to save and export the project

→ [Start Tutorial 2 — GUI](tutorial_2_gui.md)
After this tutorial: You can create and manage equivalent models in the GUI.

## 3. SOFA Coupling

Prerequisites: Tutorials 1 and 2 completed, SOFA installed and available.
Level: Intermediate.

Replace the plant with a SOFA model. 

You will learn:
- How to set up the environment for SOFA coupling
- How to interface pySimBlocks with SOFA
- How to run co-simulations
- How to use SOFA's GUI for inspection and debugging

→ [Start Tutorial 3 — SOFA Coupling](tutorial_3_sofa.md)
After this tutorial: You can run a pySimBlocks + SOFA co-simulation workflow.
