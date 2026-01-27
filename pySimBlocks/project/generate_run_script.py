# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Antoine Alessandrini
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


RUN_TEMPLATE = """\
from pathlib import Path
from pySimBlocks.core import Model, Simulator
from pySimBlocks.project.load_project_config import load_project_config
from pySimBlocks.project.plot_from_config import plot_from_config

try:
    BASE_DIR = Path(__file__).parent.resolve()
except Exception:
    BASE_DIR = Path("")

sim_cfg, model_cfg, plot_cfg = load_project_config(BASE_DIR / {parameters_path!r}{parameters_dir_line})

model = Model(
    name="model",
    model_yaml=BASE_DIR / {model_path!r},
    model_cfg=model_cfg
)

sim = Simulator(model, sim_cfg)

logs = sim.run()
if {enable_plots}:
    plot_from_config(logs, plot_cfg)
"""


def generate_python_content(
    model_yaml_path: str,
    parameters_yaml_path: str,
    parameters_dir: str | None = None,
    enable_plots: bool = True,
) -> str:

    if parameters_dir is not None:
        parameters_dir_line = f", parameters_dir=Path({parameters_dir!r})"
    else:
        parameters_dir_line = ""

    return RUN_TEMPLATE.format(
        model_path=model_yaml_path,
        parameters_path=parameters_yaml_path,
        parameters_dir_line=parameters_dir_line,
        enable_plots=enable_plots,
    )



def generate_run_script(
    *,
    project_dir: Path | None = None,
    model_yaml: Path | None = None,
    parameters_yaml: Path | None = None,
    output: Path | None = None,
) -> None:
    """
    Generate a canonical run.py script for a pySimBlocks project.

    Exactly one of the following modes must be used:
      - project_dir
      - model_yaml + parameters_yaml

    Parameters
    ----------
    project_dir : Path, optional
        Path to a project folder containing model.yaml and parameters.yaml.

    model_yaml : Path, optional
        Path to model.yaml (explicit mode).

    parameters_yaml : Path, optional
        Path to parameters.yaml (explicit mode).

    output : Path, optional
        Output run.py path (default: <project_dir>/run.py).
    """

    # ------------------------------------------------------------
    # Mode validation
    # ------------------------------------------------------------
    explicit_mode = model_yaml is not None or parameters_yaml is not None

    if project_dir and explicit_mode:
        raise ValueError(
            "Cannot use project_dir together with --model/--param."
        )

    if not project_dir and not explicit_mode:
        raise ValueError(
            "You must specify either a project directory or --model and --param."
        )

    # ------------------------------------------------------------
    # Resolve paths
    # ------------------------------------------------------------
    if project_dir:
        project_dir = Path(project_dir)
        model_yaml = project_dir / "model.yaml"
        parameters_yaml = project_dir / "parameters.yaml"
        output = output or (project_dir / "run.py")
    else:
        model_yaml = Path(model_yaml)
        parameters_yaml = Path(parameters_yaml)
        output = Path(output or "run.py")

    if not model_yaml.exists():
        raise FileNotFoundError(f"model.yaml not found: {model_yaml}")

    if not parameters_yaml.exists():
        raise FileNotFoundError(f"parameters.yaml not found: {parameters_yaml}")

    # ------------------------------------------------------------
    # Write run.py
    # ------------------------------------------------------------
    content = generate_python_content(model_yaml.name, parameters_yaml.name)

    output.write_text(content)
    print(f"[pySimBlocks] run script generated: {output}")
