# pySimBlocks

A lightweight block-diagram simulation framework for discrete-time systems in Python.

pySimBlocks allows you to build, configure, and execute discrete-time
control systems using either:

- A pure Python API
- A graphical editor (PySide6)
- YAML project configuration
- Optional SOFA and hardware integration

## Features

- Block-based modeling (Simulink-like)
- Deterministic discrete-time simulation engine
- PySide6 graphical editor
- YAML-based project serialization
- Exportable Python runner (`run.py`)
- Extensible block architecture

## Installation

### From GitHub

Install directly from GitHub using pip:
```
pip install git+https://github.com/AlessandriniAntoine/pySimBlocks
```

### Locally

Clone the repository and install locally:
```
git clone https://github.com/AlessandriniAntoine/pySimBlocks.git
cd pySimBlocks
pip install .
```

## First Steps

To open the graphical editor, run:
```bash
pysimblocks
```

### Tutorials

See the [Getting Started Guide](./docs/User_Guide/getting_started.md) for
tutorials on building your first simulation with pySimBlocks.

### Examples

A collection of basic and advanced examples is available in the
[examples](./examples) directory, including:

- Control system demonstrations
- SOFA-based simulations
- Hardware and real-time use cases
- Comparisons with external tools

See [examples/README.md](./examples/README.md) for an overview.

## Information

### License

pySimBlocks is LGPL.

LGPL refers to the GNU Lesser General Public License as published by the Free Software
Foundation; either version 3.0 of the License, or (at your option) any later 
version.

---
© 2026 Université de Lille & INRIA – Licensed under LGPL-3.0-or-later
