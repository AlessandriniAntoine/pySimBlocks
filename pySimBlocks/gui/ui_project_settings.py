import os
from pathlib import Path
import yaml
import streamlit as st


# --------------------------------------------------
# Auto-detection helpers
# --------------------------------------------------
def _auto_detect_yaml(project_dir: Path, names: list[str]) -> str | None:
    for name in names:
        path = project_dir / name
        if path.is_file():
            return str(path)

    # fallback: unique yaml
    yamls = list(project_dir.glob("*.yml")) + list(project_dir.glob("*.yaml"))
    if len(yamls) == 1:
        return str(yamls[0])

    return None


# --------------------------------------------------
# Load helpers
# --------------------------------------------------
def _load_yaml_file(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def _reset_after_load():
    st.session_state["simulation_done"] = False
    st.session_state.pop("simulation_logs", None)


# --------------------------------------------------
# Main renderer
# --------------------------------------------------
def render_project_settings():
    st.header("Project Settings")

    project_dir = Path(st.session_state.get("project_dir", ""))

    # --------------------------------------------------
    # Project folder
    # --------------------------------------------------
    with st.expander("Project folder", expanded=False):
        folder = st.text_input(
            "Project directory",
            str(project_dir) if project_dir else "",
        )

        if st.button("Set directory"):
            if folder and os.path.isdir(folder):
                st.session_state["project_dir"] = folder
                st.session_state.pop("auto_loaded_project", None)
                st.success(f"Project directory set to: {folder}")
                st.rerun()
            else:
                st.error("Invalid directory")

    if not project_dir or not project_dir.exists():
        return

    # --------------------------------------------------
    # YAML loading (parameters + model)
    # --------------------------------------------------
    with st.expander("Load project YAML", expanded=False):

        # -------- auto-detection (once) --------
        if "auto_loaded_project" not in st.session_state:
            param_auto = _auto_detect_yaml(
                project_dir,
                ["parameters.yaml", "parameters.yml"],
            )
            model_auto = _auto_detect_yaml(
                project_dir,
                ["model.yaml", "model.yml"],
            )

            if param_auto:
                st.session_state["parameters_yaml_path"] = param_auto
            if model_auto:
                st.session_state["model_yaml_path"] = model_auto

            # auto-load only if both exist
            if param_auto and model_auto:
                try:
                    st.session_state["parameters_yaml"] = _load_yaml_file(param_auto)
                    st.session_state["model_yaml"] = _load_yaml_file(model_auto)
                    _reset_after_load()
                    st.session_state["auto_loaded_project"] = True
                    st.info("Project loaded automatically from folder")
                except Exception as e:
                    st.error(f"Failed to auto-load project: {e}")

        # -------- parameters.yaml --------
        st.subheader("parameters.yaml")

        param_path = st.text_input(
            "Path",
            st.session_state.get("parameters_yaml_path", ""),
            key="parameters_yaml_path",
        )

        if st.button("Load parameters"):
            try:
                st.session_state["parameters_yaml"] = _load_yaml_file(param_path)
                _reset_after_load()
                st.success("parameters.yaml loaded")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to load parameters.yaml: {e}")

        # -------- model.yaml --------
        st.subheader("model.yaml")

        model_path = st.text_input(
            "Path",
            st.session_state.get("model_yaml_path", ""),
            key="model_yaml_path",
        )

        if st.button("Load model"):
            try:
                st.session_state["model_yaml"] = _load_yaml_file(model_path)
                _reset_after_load()
                st.success("model.yaml loaded")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to load model.yaml: {e}")
