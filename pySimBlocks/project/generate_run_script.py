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

from __future__ import annotations

import os
from pathlib import Path


# The entry point is wrapped in main() under an ``if __name__ == "__main__"``
# guard: on Windows and macOS, multiprocessing uses the "spawn" start method
# (needed by SofaPlant), which re-imports the main script in the child process.
RUN_TEMPLATE = """\
from pathlib import Path
from pySimBlocks.project import load_simulator_from_project
from pySimBlocks.project.plot_from_config import plot_from_config


def main():
    try:
        BASE_DIR = Path(__file__).parent.resolve()
    except Exception:
        BASE_DIR = Path("")

    sim, plot_cfg = load_simulator_from_project(BASE_DIR / {project_path!r})

    logs = sim.run()
    if {enable_plots} and plot_cfg is not None:
        plot_from_config(logs, plot_cfg)


if __name__ == "__main__":
    main()
"""


def generate_python_content(
    project_yaml_path: str,
    enable_plots: bool = True,
) -> str:
    """Render the run script template for a given project YAML path.

    Args:
        project_yaml_path: Path string to the project YAML file, embedded
            verbatim into the generated script. It is resolved at runtime
            relative to the directory of the generated script.
        enable_plots: Whether to include the plotting call in the script.

    Returns:
        The rendered run script as a string.
    """
    return RUN_TEMPLATE.format(
        project_path=project_yaml_path,
        enable_plots=enable_plots,
    )


def _path_relative_to_script(project_yaml: Path, output: Path) -> str:
    """Return the project path as seen from the directory of the run script.

    The generated script resolves the project path relative to its own
    location, so the embedded path must be computed from the output
    directory, not from the current working directory. Falls back to the
    absolute path when no relative path exists (e.g. different drives on
    Windows).

    Args:
        project_yaml: Path to the project YAML file.
        output: Path where the run script will be written.

    Returns:
        A POSIX-style path string to embed in the script.
    """
    project_abs = project_yaml.resolve()
    script_dir = output.resolve().parent
    try:
        rel = os.path.relpath(project_abs, script_dir)
    except ValueError:
        return project_abs.as_posix()
    return Path(rel).as_posix()


def generate_run_script(
    *,
    project_dir: Path | None = None,
    project_yaml: Path | None = None,
    output: Path | None = None,
) -> None:
    """Generate a canonical ``run.py`` script for a pySimBlocks project.

    Exactly one of ``project_dir`` or ``project_yaml`` must be provided.

    Args:
        project_dir: Path to a project folder containing ``project.yaml``.
            The output script defaults to ``<project_dir>/run.py``.
        project_yaml: Explicit path to a ``project.yaml`` file.
        output: Output path for the generated script. Defaults to
            ``<project_dir>/run.py`` in ``project_dir`` mode or ``run.py``
            in the current directory in ``project_yaml`` mode.

    Raises:
        ValueError: If both ``project_dir`` and ``project_yaml`` are given,
            or if neither is given.
        FileNotFoundError: If the resolved project YAML file does not exist.
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

    if project_dir:
        project_dir = Path(project_dir)
        project_yaml = project_dir / "project.yaml"
        output = Path(output or (project_dir / "run.py"))
    else:
        project_yaml = Path(project_yaml)
        output = Path(output or "run.py")

    if not project_yaml.exists():
        raise FileNotFoundError(f"project.yaml not found: {project_yaml}")

    content = generate_python_content(
        project_yaml_path=_path_relative_to_script(project_yaml, output)
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content)
    print(f"[pySimBlocks] run script generated: {output}")
