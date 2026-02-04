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

import os
from pathlib import Path
import shutil
from PySide6.QtCore import QProcess, QProcessEnvironment

from pySimBlocks.gui.model.project_state import ProjectState
from pySimBlocks.gui.project_controller import ProjectController
from pySimBlocks.project.generate_sofa_controller import generate_sofa_controller
from pySimBlocks.gui.services.yaml_tools import save_yaml


class SofaService:
    def __init__(self, project_state: ProjectState, project_controller: ProjectController):
        self.project_state = project_state
        self.project_controller = project_controller

        self.sofa_path = ""
        self.gui = "imgui"
        self.scene_file = ""

        self._detect_sofa()

    def get_scene_file(self):
        flag, msg, details = self.can_use_sofa()
        if flag:
            sofa_block =  [b for b in self.project_state.blocks if b.meta.type in ["sofa_plant", "sofa_exchange_i_o"]]
            scene_param = sofa_block[0].parameters.get("scene_file")
            if not scene_param:
                return False, "No scene file", "scene_file parameter is missing."

            try:
                scene_path = self._resolve_scene_file(scene_param)
            except Exception as e:
                return False, "Invalid scene file", str(e)

            if not scene_path.exists():
                return False, "Incorrect Scene File", "The scene file does not exist."

            self.scene_file = str(scene_path)
            return True, "Scene File set", ""
        else:
            return flag, msg, details

    def can_use_sofa(self):
        sofa_block =  [b for b in self.project_state.blocks if b.meta.type in ["sofa_plant", "sofa_exchange_i_o"]]
        if len(sofa_block) == 0:
            return False, "No SOFA block", "Please Add at least one sofa system."
        elif len(sofa_block) > 1:
            return False, "Multiple SOFA blocks", "Only one sofa system can be set to run sofa."
        else:
            return True, "Sofa can be master", "Only one system found. Diagram can be used from controller."

    def export_controlle(self):
        self.project_controller.save()
        generate_sofa_controller(self.project_state.directory_path)

    def run(self):
        env_ok, msg = self._check_sofa_environnment()
        if not env_ok:
            return False, "Environment error", msg

        if not self.sofa_path or not os.path.exists(self.sofa_path):
            return False, "runSofa not found", ""

        if not self.scene_file or not os.path.exists(self.scene_file):
            return False, "scene file not found", ""

        # save yaml on temp dir
        project_dir = self.project_state.directory_path
        if project_dir is None:
            return {}, False, "Project directory is not set.\nPlease define it in settings."
        temp_dir = project_dir / ".temp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)
        save_yaml(project_state=self.project_state, temp=True)
        generate_sofa_controller(temp_dir)

        # set command
        plugins = "SofaPython3"
        if self.gui == "imgui":
            plugins += ",SofaImgui"
        args = ["-l", plugins, "-g", self.gui, self.scene_file]

        self.process = QProcess()
        env = QProcessEnvironment.systemEnvironment()
        self.process.setProcessEnvironment(env)
        self.process.setProgram(self.sofa_path)
        self.process.setArguments(args)

        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.start()
        if not self.process.waitForStarted():
            return False, "Launch failed", "runSofa could not start"
        self.process.waitForFinished(-1)

        try:
            generate_sofa_controller(project_dir)
        except Exception as e:
            return False, "Could not regenerate controller", "model and parameters yaml does not exists.\n" + str(e)

        # get output results
        output = self.process.readAllStandardOutput().data().decode()
        errors = self.process.readAllStandardError().data().decode()
        full_log = output + "\n" + errors
        exit_code = self.process.exitCode()
        if exit_code != 0:
            return False, "SOFA exited with error", f"exit code = {exit_code}\n\n{full_log}"

        return True, "SOFA finished", "Process terminated correctly"

    def _check_sofa_environnment(self):
        sofa_root = os.environ.get("SOFA_ROOT")
        sofa_py3 = os.environ.get("SOFAPYTHON3_ROOT")

        if not sofa_root:
            return False, "SOFA_ROOT is not set."

        if not sofa_py3:
            return False, "SOFAPYTHON3_ROOT is not set."

        return True, "OK"

    def _detect_sofa(self):
        detected = shutil.which("runSofa")
        if not detected:
            detected = shutil.which("runsofa")
        if detected:
            self.sofa_path = detected

    def _resolve_scene_file(self, scene_file: str) -> Path:
        project_dir = self.project_state.directory_path
        if project_dir is None:
            raise RuntimeError("Project directory is not set")

        path = Path(scene_file)
        if not path.is_absolute():
            path = (project_dir / path).resolve()

        return path
