import os
import sys
import yaml
import streamlit as st

from pySimBlocks.api.codegen import generate_yaml_content

from pySimBlocks.api.ui_diagram import render_diagram
from pySimBlocks.api.ui_workspace import render_workspace
from pySimBlocks.api.ui_action import render_action
from pySimBlocks.api.ui_project_settings import render_project_settings
from pySimBlocks.api.ui_blocks import render_blocks
from pySimBlocks.api.ui_connections import render_connections
from pySimBlocks.api.ui_simulation_settings import render_simulation_settings
from pySimBlocks.api.ui_plots_definition import render_plots_definition
from pySimBlocks.api.ui_run_sim import render_results
from pySimBlocks.api.ui_codegen import render_generated_code


# ============================================================
# HELPERS
# ============================================================
path_dir = os.path.dirname(os.path.abspath(__file__))
REGISTRY_PATH = "pySimBlocks_blocks_registry.yaml"
REGISTRY_PATH = os.path.join(path_dir, REGISTRY_PATH)

def load_registry():
    with open(REGISTRY_PATH, "r") as f:
        return yaml.safe_load(f)

# -------- Automatic detection of YAML IN FOLDER --------
def auto_detect_yaml(project_dir):
    preferred = [
        "project.yaml",
        "project.yml",
        "model.yaml",
        "model.yml",
    ]

    # 1) preferred names
    for name in preferred:
        path = os.path.join(project_dir, name)
        if os.path.isfile(path):
            return path

    # 2) fallback: unique yaml
    yamls = [
        f for f in os.listdir(project_dir)
        if f.endswith((".yaml", ".yml"))
    ]

    if len(yamls) == 1:
        return os.path.join(project_dir, yamls[0])

    return None

# --------------------------------------------------
# Project directory from CLI
# --------------------------------------------------
if len(sys.argv) > 1:
    project_dir = os.path.abspath(sys.argv[1])
else:
    project_dir = os.getcwd()

if "project_dir" not in st.session_state:
    st.session_state["project_dir"] = project_dir


# ============================================================
# Initialize session state
# ============================================================
default_session_keys = {
    "yaml_data": None,
    "blocks": [],
    "connections": [],
    "plots": [],
    "edit_block_index": None,
    "edit_plot_index": None,
    "workspace": {},
    "last_result": None,
    "generated": False,
    "generated_param": None,
    "generated_model": None,
    "generated_run": None,
    "project_dir": None,
    "simulation_logs": None,
    "simulation_done": False,
}

for key, default in default_session_keys.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ============================================================
# Load registry
# ============================================================
registry = load_registry()
categories = sorted({v["category"] for v in registry.values()})


# ============================================================
# auto load yaml if in folder
# ============================================================
if "project_dir" not in st.session_state:
    st.session_state["project_dir"] = project_dir

if "auto_yaml_loaded" not in st.session_state:
    yaml_path = auto_detect_yaml(project_dir)

    if yaml_path is not None:
        try:
            with open(yaml_path, "r") as f:
                data = yaml.safe_load(f)

            st.session_state["pending_yaml"] = data
            st.session_state["auto_yaml_loaded"] = True
            st.info(f"Loaded project: {os.path.basename(yaml_path)}")
            st.rerun()

        except Exception as e:
            st.warning(f"Found YAML but failed to load it: {e}")

# ============================================================
# UI layout
# ============================================================
with st.sidebar:
    render_action()
    st.markdown("---")
    render_diagram(st.session_state["blocks"], st.session_state["connections"])
    st.markdown("---")
    render_workspace()


# ============================================================
# MAIN PAGE
# ============================================================
st.title("pySimBlocks Editor")

render_project_settings(registry)
st.markdown("---")
render_blocks(registry, categories, st.session_state["blocks"])
st.markdown("---")
render_connections(st.session_state["blocks"], st.session_state["connections"])
st.markdown("---")
dt, T = render_simulation_settings()
st.markdown("---")
logs = render_plots_definition(st.session_state["plots"])


generate_yaml_content(
    st.session_state["blocks"],
    st.session_state["connections"],
    dt, T, logs,
    st.session_state["plots"]
)

if st.session_state.get("generated", False):

    render_results()
    render_generated_code()
