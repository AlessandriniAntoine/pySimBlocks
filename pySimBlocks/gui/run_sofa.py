import os
import shutil
import subprocess
import streamlit as st
import atexit

# -------------------------------------------------------------------
# SOFA ENVIRONMENT CHECK
# -------------------------------------------------------------------

def check_sofa_environment():
    """
    Validate that SOFA env variables look correct.
    Returns (ok: bool, message: str)
    """

    sofa_root = os.environ.get("SOFA_ROOT")
    sofa_py3 = os.environ.get("SOFAPYTHON3_ROOT")

    if not sofa_root:
        return False, "SOFA_ROOT is not set."

    if not sofa_py3:
        return False, "SOFAPYTHON3_ROOT is not set."

    try:
        import Sofa
        import SofaRuntime
    except ImportError:
        return False, "SofaPython3 modules cannot be imported."

    return True, "OK"

# -------------------------------------------------------------------
# RUN SOFA
# -------------------------------------------------------------------

def run_sofa_scene(scene_file):
    """
    Launch SOFA GUI with correct plugin loading.
    The `runSofa` binary may come from PATH or user input.
    """

    # ======= 1) Validate environment ========
    env_ok, msg = check_sofa_environment()
    if not env_ok:
        st.error(f"Cannot run SOFA: {msg}")
        return

    # ======= 2) Determine runSofa binary ========
    # If user provided a custom path previously, reuse it
    runsofa = st.session_state.get("custom_runsofa", None)

    # Otherwise try PATH
    if not runsofa:
        runsofa = shutil.which("runSofa")

    if not runsofa:
        st.error("runSofa not found in PATH. Please provide its full path below.")
        return

    # Verify it exists
    if not os.path.exists(runsofa):
        st.error("The specified runSofa path is invalid.")
        return

    # ======= 3) Validate scene file ========
    final_scene_file = scene_file
    if not os.path.exists(final_scene_file):
        final_scene_file = os.path.abspath(scene_file)
        if not os.path.exists(final_scene_file):
            st.error(f"Scene file not found (in relative and absolute): {scene_file}")
        return

    # ======= 4) Build SOFA command ========
    cmd = [
        runsofa,
        "-l", "SofaImgui,SofaPython3",
        "-g", "imgui",
        final_scene_file
    ]

    env = os.environ.copy()

    try:
        proc = subprocess.Popen(cmd, env=env)
        st.session_state["sofa_process"] = proc
        st.success(f"SOFA launched with: {scene_file}")

    except Exception as e:
        st.error(f"Failed to run SOFA: {e}")


# -------------------------------------------------------------------
# STREAMLIT WIDGET BLOCK
# -------------------------------------------------------------------

def sofa_launcher_ui(scene_path):
    st.subheader("Run SOFA")

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

    # Check environment first
    env_ok, msg = check_sofa_environment()
    if not env_ok:
        st.error(f"Environment issue: {msg}")
        st.info("Please make sure you ran 'source setup.sh' of your SOFA installation.")
        return

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

    if st.button("Launch SOFA"):
        run_sofa_scene(scene_path)
