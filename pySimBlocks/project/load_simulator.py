# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
# ******************************************************************************
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
#  for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ******************************************************************************
#  Authors: see Authors.txt
# ******************************************************************************

from pathlib import Path
from typing import Tuple

from pySimBlocks.core.config import PlotConfig
from pySimBlocks.core.model import Model
from pySimBlocks.core.simulator import Simulator
from pySimBlocks.project.build_model import build_model_from_dict
from pySimBlocks.project.load_project_config import load_project_config


def load_simulator_from_project(
    project_yaml: str | Path,
) -> Tuple[Simulator, PlotConfig | None]:
    """
    Build and return a ready-to-run Simulator from a unified project.yaml.
    """
    sim_cfg, model_dict, plot_cfg, project_name, params_dir = load_project_config(
        project_yaml
    )

    model = Model(name=project_name)
    build_model_from_dict(model, model_dict, params_dir=params_dir)

    sim = Simulator(model, sim_cfg)
    return sim, plot_cfg
