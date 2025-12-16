import streamlit as st
from pySimBlocks.gui.codegen import generate_python_content
from pySimBlocks.gui.ui_run_sim import run_simulation
from pySimBlocks.gui.project_export import project_export, save_yaml_content
from pySimBlocks.gui.run_sofa import sofa_launcher_ui


def render_action():

    yaml_data = st.session_state.get("yaml_data", None)

    sofa_blocks = [
            b for b in yaml_data["blocks"]
            if b["type"].lower() in ["sofa_plant", "sofa_exchange_i_o"]
        ]

    if len(sofa_blocks) > 0:
        export_mode = st.selectbox(
            "Export mode",
            ["all", "controller-only", "cli-only"],
            index=0
        )
    else:
        export_mode = "all"

    st.header("Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Show Generated Files"):
            generate_python_content(yaml_data)

    with col2:
        if st.button("Run Simulation"):
            run_simulation(yaml_data)

    st.subheader("Saving")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save project", help="Save the editable YAML projects"):
            save_yaml_content(yaml_data)
    with col2:
        if st.button("Export Project", help="Save the project (YAML) and generate Python files for CLI execution"):
            project_export(yaml_data, export_mode)

    if len(sofa_blocks) > 0:
        scene_file = sofa_blocks[0]["scene_file"]
        sofa_launcher_ui(scene_file)
