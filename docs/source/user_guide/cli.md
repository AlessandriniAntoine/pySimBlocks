# Command Line Interface

`pySimBlocks` provides a small command line interface through the
`pysimblocks` command.

To display the available commands, run:

```bash
pysimblocks --help
```

## Launch the GUI

Use the `gui` command to open the graphical editor.

Open the current directory as a project:

```bash
pysimblocks gui
```

Open a specific project directory:

```bash
pysimblocks gui path/to/project_dir
```

If the GUI does not start, make sure `PySide6` is installed.

## Export a Python Runner

Use the `export` command to generate a `run.py` script from a `project.yaml`
file.

Export from a project directory:

```bash
pysimblocks export --directory path/to/project_dir
```

Export from a specific project file:

```bash
pysimblocks export --file path/to/project.yaml
```

Choose an explicit output path:

```bash
pysimblocks export --file path/to/project.yaml --out path/to/run.py
```

Without `--directory` or `--file`, the current directory is used as the
project directory. The two options cannot be combined. By default, the script
is written to `run.py` in the project directory (with `--directory`) or in the
current directory (with `--file`).

The generated script loads the project and runs the simulation from the command
line. It locates `project.yaml` relative to its own position, so you can move
the script together with its project as long as their relative position does
not change.

The script also works for projects using a `SofaPlant` block (see
[Tutorial 3](./tutorials/tutorial_3_sofa.md)), in which case `pySimBlocks` is the
master and SOFA runs in a separate process.

## Create a SOFA Scene and Controller

Use the `sofa-init` command to generate a starter SOFA scene and controller
pair:

```bash
pysimblocks sofa-init finger
```

This creates two files in the current directory:

- `finger_scene.py` — a SOFA scene containing the `--project-yaml` argument
  parsing, with `TODO` markers for your scene graph and the controller
  constructor arguments
- `finger_controller.py` — a `FingerController` class deriving from
  `SofaPysimBlocksController`, with empty `inputs` / `outputs` dictionaries and
  `set_inputs()` / `get_outputs()` to implement

Choose another output directory:

```bash
pysimblocks sofa-init finger --directory path/to/finger
```

Overwrite existing files:

```bash
pysimblocks sofa-init finger --force
```

The name is used for the file names and the class name. Hyphens are converted
to underscores (`my-robot` gives `my_robot_scene.py` and `MyRobotController`).
The name must be a valid Python module name once converted, otherwise the
command stops with an error.

The generated files are a starting point: fill in the scene, check that the
scene time step (`rootnode.dt`) is compatible with your project time step, and
adapt the controller to your own signals. See
[Tutorial 3](./tutorials/tutorial_3_sofa.md) for the full workflow.

## Update the Block Index

The `update` command regenerates the internal pySimBlocks block index:

```bash
pysimblocks update
```

This command is mainly useful when developing pySimBlocks itself or updating
the available block registry.
