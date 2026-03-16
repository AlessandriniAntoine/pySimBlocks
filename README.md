# pySimBlocks

[![PyPI version](https://img.shields.io/pypi/v/pySimBlocks.svg)](https://pypi.org/project/pySimBlocks/)
[![Python](https://img.shields.io/pypi/pyversions/pySimBlocks.svg)](https://pypi.org/project/pySimBlocks/)
[![License](https://img.shields.io/github/license/AlessandriniAntoine/pySimBlocks)](./LICENSE.md)
[![Documentation](https://readthedocs.org/projects/pysimblocks/badge/?version=latest)](https://pysimblocks.readthedocs.io)

---

A deterministic block-diagram simulation framework for discrete-time modeling, 
co-simulation and research prototyping in Python.

pySimBlocks allows you to build, configure, and execute discrete-time systems
using either:

- A pure Python API
- A graphical editor (PySide6)
- YAML project configuration with exportable Python runner (`run.py`)
- Optional SOFA and hardware integration

![pySimBlocks graphical editor](https://raw.githubusercontent.com/AlessandriniAntoine/pySimBlocks/main/docs/source/images/user_guide/gui_example.png)

## Installation

```bash
pip install pySimBlocks
```

Full documentation — user guide, tutorials, and API reference — is available on
[**Read the Docs**](https://pysimblocks.readthedocs.io).

## Getting Started

### Quick Example

The following example models a simple first-order low-pass filter, defined by
the difference equation:

$$ y[k] =  \alpha x[k] + (1-\alpha) y[k-1] $$

It can be implemented in pySimBlocks using the following code:

```python
from pySimBlocks import Model, Simulator, SimulationConfig, PlotConfig
from pySimBlocks.blocks.operators import Gain, Sum, Delay
from pySimBlocks.blocks.sources import WhiteNoise
from pySimBlocks.project.plot_from_config import plot_from_config

# 1. Create the blocks
noise = WhiteNoise(name="noise", std=1.0)
delay = Delay(name="delay")
filtered = Sum("filtered", signs="++")
alpha_gain = Gain(name="alpha", gain=0.1)
complement = Gain(name="complement", gain=0.9)

# 2. Build the model
model = Model("Example")
for block in [noise, delay, filtered, alpha_gain, complement]:
    model.add_block(block)

model.connect("noise", "out", "alpha", "in")
model.connect("delay", "out", "complement", "in")
model.connect("alpha", "out", "filtered", "in1")
model.connect("complement", "out", "filtered", "in2")
model.connect("filtered", "out", "delay", "in")

# 3. Simulate the model
sim_cfg = SimulationConfig(dt=0.05, T=30.)
sim = Simulator(model, sim_cfg)
logs = sim.run(logging=["noise.outputs.out", "filtered.outputs.out"])

# 4. Plot the results
plot_cfg = PlotConfig([
    {"title": "Noisy signal vs Filtered",
     "signals": ["noise.outputs.out", "filtered.outputs.out"],},
    ])
plot_from_config(logs, plot_cfg)
```

The resulting plot should look like this:

![Noise filtered](https://raw.githubusercontent.com/AlessandriniAntoine/pySimBlocks/main/docs/source/images/user_guide/quick_example.png)

See [examples/quick_start/filter.py](./examples/quick_start/filter.py)
to run the example yourself.

### Graphical Editor

The exact same model can be constructed visually using the graphical editor (as
shown in the image above of this README).

To open the graphical editor, run:
```bash
pysimblocks gui examples/quick_start/gui
```

The quick-start GUI project is stored in a single
[examples/quick_start/gui/project.yaml](./examples/quick_start/gui/project.yaml) file.

### Learning Resources


#### Tutorials

Three step-by-step tutorials are available in the
[documentation](https://pysimblocks.readthedocs.io/en/latest/user_guide/tutorials/index.html):

  | | Tutorial | Description |
  |---|---|---|
  | 1 | [Python API](https://pysimblocks.readthedocs.io/en/latest/user_guide/tutorials/tutorial_1_python.html) | Build a closed-loop PI control system in pure Python |
  | 2 | [GUI](https://pysimblocks.readthedocs.io/en/latest/user_guide/tutorials/tutorial_2_gui.html) | Build the same system visually with the graphical editor |
  | 3 | [SOFA](https://pysimblocks.readthedocs.io/en/latest/user_guide/tutorials/tutorial_3_sofa.html) | Replace the plant with a SOFA physics simulation |


#### Other Examples

A collection of basic and advanced examples is available in the
[examples](./examples) directory, including:

- Control system demonstrations
- SOFA-based simulations (tested with SOFA v24.06 and later.)
- Hardware and real-time use cases
- Comparisons with external tools

See [examples/README.md](./examples/README.md) for an overview.

## Information

### License

pySimBlocks is licensed under [LGPL-3.0-or-later](./LICENSE.md).

---
© 2026 Université de Lille & INRIA – Licensed under LGPL-3.0-or-later
