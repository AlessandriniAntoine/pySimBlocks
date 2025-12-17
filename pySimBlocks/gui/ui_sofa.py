import os
from pathlib import Path
import shutil
import subprocess
import re
import streamlit as st
from pySimBlocks.gui.ui_action import _write_yaml_files
from pySimBlocks.project.generate_sofa_controller import generate_sofa_controller


# -------------------------------------------------------------------
# SOFA ENVIRONMENT CHECK
# -------------------------------------------------------------------
def check_sofa_environment():
    sofa_root = os.environ.get("SOFA_ROOT")
    sofa_py3 = os.environ.get("SOFAPYTHON3_ROOT")

    if not sofa_root:
        return False, "SOFA_ROOT is not set."

    if not sofa_py3:
        return False, "SOFAPYTHON3_ROOT is not set."

    # Do NOT import Sofa here
    return True, "OK"

# -------------------------------------------------------------------
# RUN SOFA
# -------------------------------------------------------------------
def run_sofa_scene(scene_file):
    env_ok, msg = check_sofa_environment()
    if not env_ok:
        return False, "Environment error", msg

    runsofa = st.session_state.get("custom_runsofa") or shutil.which("runSofa")
    if not runsofa or not os.path.exists(runsofa):
        return False, "runSofa not found", ""

    gui = st.session_state.get("sofa_gui", "imgui")

    cmd = [
        runsofa,
        "-l", "SofaImgui,SofaPython3",
        "-g", gui,
        scene_file,
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            env=os.environ.copy(),
        )
        st.session_state["sofa_process"] = proc
        return True, "SOFA launched", f"GUI = {gui}"

    except Exception as e:
        return False, "Launch failed", str(e)



def update_sofa_context():
    blocks = st.session_state["model_yaml"]["blocks"]

    sofa_blocks = [
        b for b in blocks
        if b["type"] in ("sofa_plant", "sofa_exchange_i_o")
    ]

    st.session_state["nb_sofa_blocks"] = len(sofa_blocks)

    if len(sofa_blocks) == 1:
        blk = sofa_blocks[0]
        params = st.session_state["parameters_yaml"]["blocks"].get(blk["name"], {})
        st.session_state["sofa_scene_file"] = params.get("scene_file", "")
    else:
        st.session_state["sofa_scene_file"] = ""


# -------------------------------------------------------------------
# STREAMLIT WIDGET BLOCK
# -------------------------------------------------------------------
def render_sofa_launcher():
    nb_sofa_blocks = st.session_state.get("nb_sofa_blocks", 0)
    scene_file = st.session_state.get("sofa_scene_file", "")
    if nb_sofa_blocks != 1:
        return

    final_scene_file = scene_file
    if not os.path.exists(final_scene_file):
        final_scene_file = os.path.abspath(scene_file)
        if not os.path.exists(final_scene_file):
            st.error(f"Scene file not found (in relative and absolute): {scene_file}")
        return

    st.header("Run SOFA")

    p = st.session_state.get("sofa_process", None)
    if p is not None:
        code = p.poll()

        if code is not None:
            try:
                p.terminate()
                p.wait(timeout=0.2)
            except Exception:
                pass

            st.session_state["sofa_process"] = None

    env_ok, msg = check_sofa_environment()
    if not env_ok:
        st.error(f"Cannot run SOFA: {msg}")
        return

    col_run, col_runsofa, col_viewer = st.columns(3)

    with col_runsofa:
        # Try to auto-detect runSofa
        detected = shutil.which("runSofa")
        if not detected:
            detected = shutil.which("runsofa")

        custom = st.session_state.get("custom_runsofa", "")
        if detected:
            st.write("runSofa detected")
        else:
            runsofa_input = st.text_input(
                "(runSofa not found) Custom path:",
                value=custom if custom else "",
                help="Leave empty to use the runSofa found in PATH."
            )
            if runsofa_input.strip():
                st.session_state["custom_runsofa"] = runsofa_input.strip()

    with col_viewer:
        gui = st.selectbox(
            "SOFA Viewer",
            options=["imgui", "qglviewer", "qt", "custom"],
            index=0,
            help="Select SOFA graphical user interface"
        )
        if gui == "custom":
            gui = st.text_input("Gui name", "imgui")
        st.session_state["sofa_gui"] = gui

    with col_run:
        if st.button("runSOFA"):
            project_dir = st.session_state.get("project_dir")
            if not project_dir:
                st.session_state["sofa_status"] = {
                    "state": "error",
                    "message": "Project directory not set",
                    "details": ""
                }
                st.rerun()

            project_dir = Path(project_dir)
            temp_dir = project_dir / ".temp"

            _write_yaml_files(temp_dir, temp=True)
            generate_sofa_controller(temp_dir)

            ok, msg, details = run_sofa_scene(final_scene_file)

            st.session_state["sofa_status"] = {
                "state": "running" if ok else "error",
                "message": msg,
                "details": details,
            }

            st.rerun()

        status = st.session_state.get("sofa_status")

        if status:
            if status["state"] == "running":
                st.success(status["message"])
                if status["details"]:
                    st.caption(status["details"])

            elif status["state"] == "error":
                st.error(status["message"])
                if status["details"]:
                    st.code(status["details"], language="text")
