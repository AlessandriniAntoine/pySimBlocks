from pySimBlocks.core import Model, Simulator
from pySimBlocks.project.load_project_config import load_project_config
from pySimBlocks.project.plot_from_config import plot_from_config

sim_cfg, model_cfg, plot_cfg = load_project_config("parameters.yaml")

model = Model(
    name="model",
    model_yaml="model.yaml",
    model_cfg=model_cfg
)

sim = Simulator(model, sim_cfg, verbose=True)

logs = sim.run()
if True:
    plot_from_config(logs, plot_cfg)
