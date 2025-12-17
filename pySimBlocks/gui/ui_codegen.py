import streamlit as st
from pySimBlocks.gui.helpers import dump_yaml, dump_model_yaml


def render_codegen():
    st.header("Generated Files")
    params_yaml = st.session_state.get("parameters_yaml", {})
    model_yaml = st.session_state.get("model_yaml", {})

    col_param, col_model = st.columns(2)
    with col_param:
        with st.expander("parameters.yaml"):
            st.code(dump_yaml(params_yaml), language="yaml")

    with col_model:
        with st.expander("model.yaml"):
            st.code(dump_model_yaml(model_yaml), language="yaml")
