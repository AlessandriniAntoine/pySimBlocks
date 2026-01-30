import os
import shutil
import sys
from pySimBlocks.gui.model import ProjectState
from pySimBlocks.gui.services.yaml_tools import save_yaml
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
        
        temp_dir = project_dir / ".temp"

        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)
        save_yaml(project_state, temp=True)

        model_path = temp_dir / "model.yaml"
        param_path = temp_dir / "parameters.yaml"

        code = generate_python_content(
            model_yaml_path=str(model_path),
            parameters_yaml_path=str(param_path),
            parameters_dir=str(project_dir),
            enable_plots=False,
        )

        old_cwd = os.getcwd()
        old_sys_path = list(sys.path)
        env = {}
        try:
            os.chdir(temp_dir)
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