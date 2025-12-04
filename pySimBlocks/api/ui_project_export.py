import streamlit as st
import yaml
import os

def render_project_export(yaml_data, param_str, model_str, run_str):

    st.subheader("Export Project")

    project_dir = st.session_state.get("project_dir", None)
    if not project_dir:
        st.error("Please set a project directory first.")
        return

    if st.button("Export to folder"):

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
