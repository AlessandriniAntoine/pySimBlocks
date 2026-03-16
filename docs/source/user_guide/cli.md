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

This generated script rebuilds the model and runs the simulation from the
command line.

## Export a SOFA Controller

If your project uses SOFA integration, you can update the SOFA controller
generated from `project.yaml`:

```bash
pysimblocks export --directory path/to/project_dir --sofa-controller
```

You can also target a specific project file:

```bash
pysimblocks export --file path/to/project.yaml --sofa-controller
```

If this command fails, check your SOFA integration setup and the associated
project files.

## Update the Block Index

The `update` command regenerates the internal pySimBlocks block index:

```bash
pysimblocks update
```

This command is mainly useful when developing pySimBlocks itself or updating
the available block registry.
