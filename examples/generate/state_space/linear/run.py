from pathlib import Path
from pySimBlocks.core import Model, Simulator
from pySimBlocks.project.load_project_config import load_project_config
from pySimBlocks.project.plot_from_config import plot_from_config

try:
    BASE_DIR = Path(__file__).parent.resolve()
except Exception:
    BASE_DIR = Path("")

sim_cfg, model_cfg, plot_cfg = load_project_config(BASE_DIR / 'parameters.yaml')

model = Model(
    name="model",
    model_yaml=BASE_DIR / 'model.yaml',
    model_cfg=model_cfg
)

sim = Simulator(model, sim_cfg)

logs = sim.run()
if True:
    plot_from_config(logs, plot_cfg)
