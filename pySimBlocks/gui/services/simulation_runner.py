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

import os
import sys
from pySimBlocks.gui.models import ProjectState
from pySimBlocks.gui.services.yaml_tools import (
    cleanup_runtime_project_yaml,
    runtime_project_yaml_path,
    save_yaml,
)
from pySimBlocks.project.generate_run_script import generate_python_content


class SimulationRunner:
    def run(self, project_state: ProjectState):
        project_dir = project_state.directory_path
        if project_dir is None:
            return (
                {},
                False,
                "Project directory is not set.\nPlease define it in settings.",
            )

        project_path = runtime_project_yaml_path(project_dir)
        cleanup_runtime_project_yaml(project_dir)
        save_yaml(project_state, runtime=True)

        code = generate_python_content(
            project_yaml_path=str(project_path),
            enable_plots=False,
        )

        old_cwd = os.getcwd()
        old_sys_path = list(sys.path)
        env = {}
        try:
            os.chdir(project_dir)
            sys.path.insert(0, str(project_dir))
            exec(code, env, env)
            logs = env.get("logs")
            return logs, True, "Simulation success."
        except Exception as e:
            logs = {}
            return logs, False, f"Error: {e}"
        finally:
            os.chdir(old_cwd)
            sys.path[:] = old_sys_path
            cleanup_runtime_project_yaml(project_dir)
