import streamlit as st
import numpy as np
from fractions import Fraction

from pySimBlocks.api.utils import load_registry
from pySimBlocks.api.ui_diagram import render_diagram
from pySimBlocks.api.ui_blocks import render_block_form, render_block_list
from pySimBlocks.api.ui_connections import render_connections
from pySimBlocks.api.ui_plots import render_plots
from pySimBlocks.api.ui_yaml import render_yaml_export
from pySimBlocks.api.ui_codegen import render_codegen
from pySimBlocks.api.ui_workspace import render_workspace
from pySimBlocks.api.ui_project_export import render_project_export
from pySimBlocks.api.ui_run_sim import render_run_sim
from pySimBlocks.api.ui_load_yaml import render_load_yaml


# ============================================================
# Initialize session state
# ============================================================
default_session_keys = {
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
# UI layout
# ============================================================
with st.sidebar:

    # 1) Load project
    st.header("Load project")
    render_load_yaml(registry)

    st.markdown("---")

    # 2) Project folder
    st.header("Project folder")
    folder = st.text_input("Project directory", st.session_state["project_dir"] or "")
    if st.button("Set directory"):
        if folder:
            st.session_state["project_dir"] = folder
            st.success(f"Project directory set to: {folder}")
            st.rerun()

    st.markdown("---")

    # 3) Live diagram
    st.header("Diagram")
    render_diagram(st.session_state["blocks"], st.session_state["connections"])

    st.markdown("---")

    # 4) Workspace
    st.header("Workspace")
    render_workspace()


# ============================================================
# MAIN PAGE
# ============================================================
st.title("pySimBlocks Editor")


render_block_form(registry, categories, st.session_state["blocks"])
render_block_list(st.session_state["blocks"])
render_connections(st.session_state["blocks"], st.session_state["connections"])

st.header("Simulation Settings")
dt_raw = st.text_input("dt", value=st.session_state.get("dt_raw", "0.01"))
T_raw  = st.text_input("T",  value=st.session_state.get("T_raw", "2.0"))

def parse_value(expr):
    expr = expr.strip()

    try:
        return float(Fraction(expr))
    except Exception:
        pass
    try:
        return float(eval(expr, {"__builtins__": {}}, {"np": np}))
    except Exception:
        st.error(f"Cannot parse value: {expr}")
        return None


dt = parse_value(dt_raw)
T = parse_value(T_raw)

signals = [
    f"{b['name']}.outputs.{p}"
    for b in st.session_state["blocks"]
    for p in b["computed_outputs"]
]

logs = st.multiselect("Signals to log", signals, default=st.session_state.get("logs_loaded", []))

render_plots(st.session_state["plots"], logs)

yaml_data = render_yaml_export(
    st.session_state["blocks"],
    st.session_state["connections"],
    dt, T, logs,
    st.session_state["plots"]
)


# ============================================================
# CODE GENERATION
# ============================================================
generated = render_codegen(yaml_data)

if generated:
    param = st.session_state["generated_param"]
    model = st.session_state["generated_model"]
    run   = st.session_state["generated_run"]

    # Buttons ABOVE file contents
    render_run_sim(param, model, yaml_data)
    render_project_export(yaml_data, param, model, run)

    st.subheader("parameters_auto.py")
    with st.expander("File content"):
        st.code(param, language="python")

    st.subheader("model.py")
    with st.expander("File content"):
        st.code(model, language="python")

    st.subheader("run.py")
    with st.expander("File content"):
        st.code(run, language="python")
