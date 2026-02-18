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


RUN_TEMPLATE = """\
from pathlib import Path
from pySimBlocks.project import load_simulator_from_project
from pySimBlocks.project.plot_from_config import plot_from_config

try:
    BASE_DIR = Path(__file__).parent.resolve()
except Exception:
    BASE_DIR = Path("")

sim, plot_cfg = load_simulator_from_project(BASE_DIR / {project_path!r})

logs = sim.run()
if {enable_plots} and plot_cfg is not None:
    plot_from_config(logs, plot_cfg)
"""

def generate_python_content(
    project_yaml_path: str,
    enable_plots: bool = True,
) -> str:
    return RUN_TEMPLATE.format(
        project_path=project_yaml_path,
        enable_plots=enable_plots,
    )



def generate_run_script(
    *,
    project_dir: Path | None = None,
    project_yaml: Path | None = None,
    output: Path | None = None,
) -> None:
    """
    Generate a canonical run.py script for a pySimBlocks project.

    Exactly one of the following modes must be used:
      - project_dir (project.yaml expected)
      - project_yaml
      - model_yaml + parameters_yaml

    Parameters
    ----------
    project_dir : Path, optional
        Path to a project folder containing project.yaml.

    project_yaml : Path, optional
        Path to project.yaml (explicit unified mode).

    output : Path, optional
        Output run.py path (default: <project_dir>/run.py).
    """

    has_project_yaml_mode = project_yaml is not None

    if project_dir and has_project_yaml_mode:
        raise ValueError(
            "Cannot use project_dir with project_yaml."
        )

    if not project_dir and not has_project_yaml_mode:
        raise ValueError(
            "You must specify one mode: project_dir or project_yaml."
        )

    # Unified project_dir mode
    if project_dir:
        project_dir = Path(project_dir)
        project_yaml = project_dir / "project.yaml"
        output = output or (project_dir / "run.py")
        if not project_yaml.exists():
            raise FileNotFoundError(f"project.yaml not found: {project_yaml}")

        content = generate_python_content(project_yaml_path=project_yaml.name)

    # Unified explicit project_yaml mode
    elif has_project_yaml_mode:
        project_yaml = Path(project_yaml)
        output = Path(output or "run.py")
        if not project_yaml.exists():
            raise FileNotFoundError(f"project.yaml not found: {project_yaml}")

        content = generate_python_content(project_yaml_path=str(project_yaml))

    output.write_text(content)
    print(f"[pySimBlocks] run script generated: {output}")
