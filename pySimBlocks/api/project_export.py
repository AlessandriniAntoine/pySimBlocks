import streamlit as st
import yaml
import os
from pySimBlocks.api.codegen import generate_python_content


def project_export(yaml_data):

    project_dir = st.session_state.get("project_dir", None)
    if not project_dir:
        st.error("Please set a project directory first.")
        return

    generate_python_content(yaml_data)
    param_str = st.session_state["generated_param"]
    model_str = st.session_state["generated_model"]
    run_str = st.session_state["generated_run"]

    os.makedirs(project_dir, exist_ok=True)

    with open(os.path.join(project_dir, "project.yaml"), "w") as f:
        f.write(yaml.dump(yaml_data, sort_keys=False))

    with open(os.path.join(project_dir, "parameters_auto.py"), "w") as f:
        f.write(param_str)

    with open(os.path.join(project_dir, "model.py"), "w") as f:
        f.write(model_str)

    with open(os.path.join(project_dir, "run.py"), "w") as f:
        f.write(run_str)

    st.success(f"Exported to {project_dir}")


def save_yaml_content(yaml_data):
    project_dir = st.session_state.get("project_dir", None)
    if not project_dir:
        st.error("Please set a project directory first.")
        return

    os.makedirs(project_dir, exist_ok=True)

    with open(os.path.join(project_dir, "project.yaml"), "w") as f:
        f.write(yaml.dump(yaml_data, sort_keys=False))

    st.success(f"Exported to {project_dir}")
