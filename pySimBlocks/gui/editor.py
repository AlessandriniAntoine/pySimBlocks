import os
import sys
import atexit
import shutil
from pathlib import Path
import streamlit as st

from pySimBlocks.gui.ui_action import render_action
from pySimBlocks.gui.ui_blocks import render_blocks
from pySimBlocks.gui.ui_codegen import render_codegen
from pySimBlocks.gui.ui_connections import render_connections, compute_available_outputs
from pySimBlocks.gui.ui_diagram import render_diagram
from pySimBlocks.gui.ui_external_param import render_external_paramaters
from pySimBlocks.gui.ui_plot_results import render_plot_results
from pySimBlocks.gui.ui_plot_settings import render_plot_settings
from pySimBlocks.gui.ui_project_settings import render_project_settings
from pySimBlocks.gui.ui_simulation_settings import render_simulation_settings
from pySimBlocks.gui.ui_sofa import render_sofa_launcher, update_sofa_context
from pySimBlocks.tools.blocks_registry import load_block_registry


@st.cache_data
def _load_registry():
    return load_block_registry()
registry = _load_registry()
categories = sorted(registry.keys())

# --------------------------------------------------
# Project directory from CLI
# --------------------------------------------------
if len(sys.argv) > 1:
    project_dir = os.path.abspath(sys.argv[1])
else:
    project_dir = os.getcwd()

if "project_dir" not in st.session_state:
    st.session_state["project_dir"] = project_dir

# --------------------------------------------------
# INITIALIZE KEYS
# --------------------------------------------------
default_session_keys = {
    "parameters_yaml": {'simulation': {}, 'blocks': {}, 'logging': [], 'plots': []},
    "model_yaml": {'blocks': [], 'connections': []},
    "edit_block": None,
    "project_dir": "",
    "simulation_done": False
}

for key, default in default_session_keys.items():
    if key not in st.session_state:
        st.session_state[key] = default


# --------------------------------------------------
# Main
# --------------------------------------------------
st.title("pySimBlocks Editor")
render_project_settings()
st.divider()
render_blocks(registry, categories)
st.divider()
render_connections(registry)
st.session_state["available_outputs"] = compute_available_outputs(registry)
st.divider()
render_simulation_settings()
st.divider()
render_plot_settings()
st.divider()
render_plot_results()
st.divider()
render_codegen()

update_sofa_context()


# --------------------------------------------------
# SIDE BAR
# --------------------------------------------------
with st.sidebar:
    render_action()
    st.divider()
    render_sofa_launcher()
    st.divider()
    render_diagram()
    st.divider()
    render_external_paramaters()


def _cleanup_temp():
    project_dir = st.session_state.get("project_dir")
    if project_dir:
        temp = Path(project_dir) / ".temp"
        if temp.exists():
            shutil.rmtree(temp)

atexit.register(_cleanup_temp)
