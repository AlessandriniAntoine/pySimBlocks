import shutil
import os
from pathlib import Path

import streamlit as st

from pySimBlocks.gui_new.helpers import dump_yaml, dump_model_yaml
from pySimBlocks.project.generate_run_script import generate_python_content


# ===============================================================
# Public entry point
# ===============================================================

def render_action():
    st.header("Actions")

    col_run, col_save, col_export = st.columns(3)

    with col_run:
        if st.button("Run Simulation", help="Run simulation in a temporary folder"):
            _run_simulation()
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

    _write_yaml_files(temp_dir)

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

    except Exception as e:
        st.session_state["simulation_done"] = False
        st.session_state["simulation_status"] = {
            "state": "error",
            "message": str(e),
        }

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

    model_path = project_dir / "model.yaml"
    param_path = project_dir / "parameters.yaml"

    run_py = project_dir / "run.py"
    run_py.write_text(
        generate_python_content(
            model_yaml_path=str(model_path),
            parameters_yaml_path=str(param_path),
        )
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


def _write_yaml_files(directory: Path):
    params_yaml = st.session_state.get("parameters_yaml", {})
    model_yaml = st.session_state.get("model_yaml", {})

    directory.mkdir(parents=True, exist_ok=True)

    (directory / "parameters.yaml").write_text(
        dump_yaml(params_yaml)
    )
    (directory / "model.yaml").write_text(
        dump_model_yaml(model_yaml)
    )
