import shutil
import os
from pathlib import Path
import copy

import streamlit as st

from pySimBlocks.gui.helpers import dump_yaml, dump_model_yaml
from pySimBlocks.project.generate_run_script import generate_python_content
from pySimBlocks.project.generate_sofa_controller import generate_sofa_controller


# ===============================================================
# Public entry point
# ===============================================================

def render_action():
    st.header("Actions")

    col_run, col_save, col_export = st.columns(3)

    with col_run:
        if st.button("Run Simulation", help="Run simulation in a temporary folder"):
            ok = _run_simulation()
            st.rerun()
        status = st.session_state.get("simulation_status")
        if status:
            if status["state"] == "running":
                st.info("Simulation running…")
            elif status["state"] == "success":
                st.success(status["message"])
            elif status["state"] == "error":
                st.error(f"Simulation failed: {status['message']}")

    with col_save:
        if st.button("Save YAML", help="Save model.yaml and parameters.yaml"):
            _save_project_yaml()

    with col_export:
        if st.button(
            "Export project",
            help="Save YAML and generate run.py for CLI execution",
        ):
            _export_project()

        if st.session_state.get("nb_sofa_blocks", 0) == 1:
            if st.button("Export Controller", help="Save YAML and Write path on Controller."):
                _export_sofa_controller()


# ===============================================================
# Core actions
# ===============================================================
def _run_simulation():
    project_dir = _get_project_dir()
    if project_dir is None:
        return

    # --------------------------------------------------
    # Init status
    # --------------------------------------------------
    st.session_state["simulation_status"] = {
        "state": "running",
        "message": None,
    }

    temp_dir = project_dir / ".temp"

    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    _write_yaml_files(temp_dir, True)

    model_path = temp_dir / "model.yaml"
    param_path = temp_dir / "parameters.yaml"

    code = generate_python_content(
        model_yaml_path=str(model_path),
        parameters_yaml_path=str(param_path),
        enable_plots=False
    )

    old_cwd = os.getcwd()
    try:
        env = {}
        os.chdir(temp_dir)

        exec(code, env, env)

        logs = env.get("logs")
        if logs is None:
            raise RuntimeError("Simulation did not produce logs")

        st.session_state["simulation_logs"] = logs
        st.session_state["simulation_done"] = True
        st.session_state["simulation_status"] = {
            "state": "success",
            "message": "Simulation completed successfully.",
        }
        return True

    except Exception as e:
        st.session_state["simulation_done"] = False
        st.session_state["simulation_status"] = {
            "state": "error",
            "message": str(e),
        }
        return False

    finally:
        os.chdir(old_cwd)



def _save_project_yaml():
    project_dir = _get_project_dir()
    if project_dir is None:
        return

    _write_yaml_files(project_dir)
    st.success("YAML files saved")


def _export_project():
    project_dir = _get_project_dir()
    if project_dir is None:
        return

    _write_yaml_files(project_dir)

    run_py = project_dir / "run.py"
    run_py.write_text(
        generate_python_content(
            model_yaml_path="model.yaml",
            parameters_yaml_path="parameters.yaml",
        )
    )

    st.success("Project exported (YAML + run.py)")


def _export_sofa_controller():
    project_dir = _get_project_dir()
    if project_dir is None:
        return

    _write_yaml_files(project_dir)
    generate_sofa_controller(
        project_dir,
    )

    st.success("Project exported (YAML + run.py)")


# ===============================================================
# Helpers
# ===============================================================

def _get_project_dir() -> Path | None:
    project_dir = st.session_state.get("project_dir")
    if not project_dir:
        st.error("Please set a project directory first.")
        return None
    return Path(project_dir)


def _write_yaml_files(directory: Path, temp=False):
    params_yaml = st.session_state.get("parameters_yaml", {})
    model_yaml = st.session_state.get("model_yaml", {})

    if temp and "external" in params_yaml:
        params_yaml = copy.deepcopy(params_yaml)
        external_path = Path(params_yaml["external"]).resolve()
        relative_external = os.path.relpath(external_path, directory)
        params_yaml["external"] = relative_external

    directory.mkdir(parents=True, exist_ok=True)

    (directory / "parameters.yaml").write_text(
        dump_yaml(params_yaml)
    )
    (directory / "model.yaml").write_text(
        dump_model_yaml(model_yaml)
    )
