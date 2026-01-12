from pySimBlocks.project.load_simulation_config import load_simulation_config, _load_yaml


from pathlib import Path
from typing import Tuple
from pySimBlocks.core.config import SimulationConfig, ModelConfig, PlotConfig


def load_project_config(
    parameters_yaml: str | Path,
    parameters_dir: Path | None = None,
) -> Tuple[SimulationConfig, ModelConfig, PlotConfig | None]:
    """
    Load a full pySimBlocks project configuration.

    This function parses:
      - simulation configuration,
      - model numerical parameters,
      - optional plot configuration.

    Parameters:
        parameters_yaml: path to parameters.yaml

    Returns:
        (SimulationConfig, ModelConfig, PlotConfig or None)
    """
    sim_cfg, model_cfg = load_simulation_config(parameters_yaml, parameters_dir)

    raw = _load_yaml(Path(parameters_yaml))

    plots_data = raw.get("plots", None)
    plot_cfg = None

    if plots_data is not None:
        if not isinstance(plots_data, list):
            raise ValueError("'plots' section must be a list")

        plot_cfg = PlotConfig(plots=plots_data)
        plot_cfg.validate()

    return sim_cfg, model_cfg, plot_cfg
