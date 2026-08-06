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
import shutil
from pathlib import Path
from typing import Callable

import numpy as np

from PySide6.QtCore import QProcess, QProcessEnvironment

from pySimBlocks.gui.models.project_state import ProjectState
from pySimBlocks.gui.project_controller import ProjectController
from pySimBlocks.gui.services.yaml_tools import (
    cleanup_runtime_project_yaml,
    runtime_project_yaml_path,
    save_yaml,
)


def sofa_logs_npz_path(project_dir: Path) -> Path:
    """Path to the temporary logs dump written by the SOFA controller."""
    return project_dir / ".sofa_logs.npz"


def cleanup_sofa_logs_npz(project_dir: Path | None) -> None:
    if project_dir is None:
        return
    npz = sofa_logs_npz_path(project_dir)
    if npz.exists():
        npz.unlink(missing_ok=True)


class SofaService:
    """Manage SOFA-specific validation, export, and execution workflows.

    Attributes:
        project_state: Project state used to resolve blocks and files.
        project_controller: Controller used to access current view state.
        sofa_path: Path to the ``runSofa`` executable.
        gui: Selected SOFA GUI backend.
        scene_file: Resolved SOFA scene file path.
    """

    def __init__(self, project_state: ProjectState, project_controller: ProjectController):
        """Initialize the SOFA service.

        Args:
            project_state: Project state used to resolve blocks and files.
            project_controller: Controller used to access current view state.

        Raises:
            None.
        """
        self.project_state = project_state
        self.project_controller = project_controller

        self.sofa_path = ""
        self.gui = "imgui"
        self.scene_file = ""
        self.on_early_warning = None
        self.logs: dict = {}
        self.on_finished: Callable | None = None

        self._detect_sofa()


    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------
    def get_scene_file(self):
        """Resolve and cache the scene file used by the SOFA block.

        Returns:
            Tuple containing success flag, title, and details message.
        """
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
        """Check whether the current project can be driven by SOFA.

        Returns:
            Tuple containing success flag, title, and details message.
        """
        sofa_block =  [b for b in self.project_state.blocks if b.meta.type in ["sofa_plant", "sofa_exchange_i_o"]]
        if len(sofa_block) == 0:
            return False, "No SOFA block", "Please Add at least one sofa system."
        elif len(sofa_block) > 1:
            return False, "Multiple SOFA blocks", "Only one sofa system can be set to run sofa."
        else:
            return True, "Sofa can be master", "Only one system found. Diagram can be used from controller."

    def run(self):
        """Run the configured SOFA scene and collect its execution output.

        Returns:
            Tuple containing success flag, title, and details message.
        """
        env_ok, msg = self._check_sofa_environnment()
        if not env_ok:
            return False, "Environment error", msg

        if not self.sofa_path or not os.path.exists(self.sofa_path):
            return False, "runSofa not found", ""

        if not self.scene_file or not os.path.exists(self.scene_file):
            return False, "scene file not found", ""

        project_dir = self.project_state.directory_path
        if project_dir is None:
            return {}, False, "Project directory is not set.\nPlease define it in settings."

        runtime_yaml = runtime_project_yaml_path(project_dir)
        cleanup_runtime_project_yaml(project_dir)
        save_yaml(project_state=self.project_state, runtime=True)
        self._expected_yaml = runtime_yaml
        self._project_yaml_checked = False
        self.logs = {}

        # set command
        plugins = "SofaPython3"
        if self.gui == "imgui":
            plugins += ",SofaImgui"
        args = ["-l", plugins, "-g", self.gui, self.scene_file,
            "--argv", f"--project-yaml,{runtime_yaml}"]

        self._full_log = ""

        self.process = QProcess()
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYSIMBLOCKS_SOFA_DUMP_LOGS", "1")
        self.process.setProcessEnvironment(env)
        self.process.setWorkingDirectory(str(Path(self.scene_file).parent))
        self.process.setProgram(self.sofa_path)
        self.process.setArguments(args)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(
            lambda: self._accumulate_output()
        )

        try:
            self.process.start()
            if not self.process.waitForStarted():
                return False, "Launch failed", "runSofa could not start"
            self.process.waitForFinished(-1)

            # get output results
            full_log = self._full_log
            exit_code = self.process.exitCode()
            if exit_code != 0:
                return False, "SOFA exited with error", f"exit code = {exit_code}\n\n{full_log}"

            pysimblocks_errors = [
                line for line in full_log.splitlines()
                if "[pySimBlocks] ERROR" in line
            ]
            if pysimblocks_errors:
                return False, "pySimBlocks configuration error", "\n".join(pysimblocks_errors)

            warning = self._check_project_yaml_used(full_log, runtime_yaml)
            if warning:
                return False, "Project YAML mismatch", warning

            load_status, msg = self._load_logs(project_dir)
            if not load_status:
                return False, "SOFA finished but logs not found", msg

            return True, "SOFA finished", "Process terminated correctly"

        finally:
            cleanup_runtime_project_yaml(project_dir)
            cleanup_sofa_logs_npz(project_dir)

    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------
    def _accumulate_output(self):
        """Append the latest process output chunk to the accumulated log."""
        chunk = self.process.readAllStandardOutput().data().decode()
        print(chunk, end="")
        self._full_log += chunk
        
        if not self._project_yaml_checked:
            self._maybe_check_project_yaml_now()

    def _check_sofa_environnment(self):
        """Validate the environment variables required to run SOFA."""
        sofa_root = os.environ.get("SOFA_ROOT")
        if not sofa_root:
            return False, "SOFA_ROOT is not set."

        return True, "OK"

    def _detect_sofa(self):
        """Detect the ``runSofa`` executable from environment or PATH."""
        detected = None
        sofa_root = os.environ.get("SOFA_ROOT")
        if sofa_root:
            bin_dir = Path(sofa_root) / "bin"
            for candidate in ("runSofa", "runSofa.exe"):
                potential_path = bin_dir / candidate
                if potential_path.exists():
                    detected = str(potential_path)
                    break

        if not detected:
            detected = shutil.which("runSofa")
        
        if not detected:
            detected = shutil.which("runsofa")

        if detected:
            self.sofa_path = detected

    def _resolve_scene_file(self, scene_file: str) -> Path:
        """Resolve a scene file path relative to the project directory."""
        project_dir = self.project_state.directory_path
        if project_dir is None:
            raise RuntimeError("Project directory is not set")

        path = Path(scene_file).expanduser()
        if not path.is_absolute():
            path = (project_dir / path).resolve()

        return path

    def _check_project_yaml_used(self, full_log: str, expected_yaml: Path) -> str | None:
        """Check the log for a project_yaml mismatch or missing confirmation.

        Args:
            full_log: Accumulated stdout/stderr from the runSofa process.
            expected_yaml: The runtime project.yaml path that was passed via
                --argv for this run.

        Returns:
            A warning message if the controller's project_yaml doesn't match
            or was never logged, otherwise None.
        """
        prefix = "[pySimBlocks] Controller using project_yaml: "
        used_lines = [
            line[len(prefix):].strip()
            for line in full_log.splitlines()
            if line.strip().startswith(prefix)
        ]

        if not used_lines:
            return (
                "The scene's controller did not report which project.yaml it used.\n"
                "This usually means the scene's createScene() does not forward "
                "--project-yaml to the controller (see the SOFA scaffold template)."
            )

        used_yaml = Path(used_lines[-1]).resolve()
        if used_yaml != Path(expected_yaml).resolve():
            return (
                "The controller used a different project.yaml than expected:\n"
                f"  Expected: {expected_yaml}\n"
                f"  Used:     {used_yaml}\n\n"
                "Your GUI edits may not have been reflected in this run.\n" 
                "This usually means the scene's createScene() does not forward"
                "--project-yaml to the controller (see the SOFA scaffold template).\n\n"
                "You can create scene and controller template using `pysimblocks sofa-init`" 
                "and compare it to your scene's createScene() function."
            )

        return None

    def _maybe_check_project_yaml_now(self):
        """Check project_yaml as soon as the controller's confirmation line appears."""
        prefix = "[pySimBlocks] Controller using project_yaml: "
        if prefix not in self._full_log:
            return

        self._project_yaml_checked = True
        warning = self._check_project_yaml_used(self._full_log, self._expected_yaml)
        if warning and self.on_early_warning:
            self.on_early_warning(warning)

    def _load_logs(self, project_dir: Path) -> tuple[bool, str]:
        """Load logs dumped by the SOFA controller, if present."""
        npz_path = sofa_logs_npz_path(project_dir)
        if not npz_path.exists():
            self.logs = {}
            return False, "No logs found"
        try:
            with np.load(npz_path, allow_pickle=True) as data:
                logs = {}
                for k in data.files:
                    arr = data[k]
                    if k == "time":
                        logs[k] = arr
                    else:
                        logs[k] = [arr[i] for i in range(arr.shape[0])]
                self.logs = logs
                return True, "Logs loaded"
        except Exception as e:
            self.logs = {}
            return False, f"Failed to load logs: {e}"
