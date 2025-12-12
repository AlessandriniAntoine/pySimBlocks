import streamlit as st
from pySimBlocks.api.codegen import generate_python_content
from pySimBlocks.api.ui_run_sim import run_simulation
from pySimBlocks.api.project_export import project_export, save_yaml_content


def render_action():

    yaml_data = st.session_state.get("yaml_data", None)

    st.header("Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Show Generated Files"):
            generate_python_content(yaml_data)

    with col2:
        if st.button("Run Simulation"):
            run_simulation(yaml_data)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save project", help="Save the editable YAML projects"):
            save_yaml_content(yaml_data)
    with col2:
        if st.button("Export Project", help="Save the project (YAML) and generate Python files for CLI execution"):
            project_export(yaml_data)
