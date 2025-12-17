from pySimBlocks.project.load_project_config import load_project_config
from pySimBlocks.core.model import Model
from pySimBlocks.core.simulator import Simulator
from pySimBlocks.project.plot_from_config import plot_from_config

# Load configs
sim_cfg, model_cfg, plot_cfg = load_project_config("parameters.yaml")

# Build model
model = Model(
    name="open_loop",
    model_yaml="model.yaml",
    model_cfg=model_cfg
)

# Create simulator
sim = Simulator(model, sim_cfg)

# Run
logs = sim.run()
plot_from_config(logs, plot_cfg)
