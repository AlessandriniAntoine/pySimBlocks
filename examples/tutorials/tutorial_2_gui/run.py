from pathlib import Path
from pySimBlocks.project import load_simulator_from_project
from pySimBlocks.project.plot_from_config import plot_from_config

try:
    BASE_DIR = Path(__file__).parent.resolve()
except Exception:
    BASE_DIR = Path("")

sim, plot_cfg = load_simulator_from_project(BASE_DIR / 'project.yaml')

logs = sim.run()
if True and plot_cfg is not None:
    plot_from_config(logs, plot_cfg)
