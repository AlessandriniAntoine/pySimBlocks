import streamlit as st


def render_external_paramaters():
    st.header("External Python Parameters")
    path = st.text_input("Relative path to python file containing parametes")
    params_yaml = st.session_state.get("parameters_yaml", {})

    if path != "" and path.endswith(".py"):
        params_yaml["external"] = path

        st.session_state["parameters_yaml"] = params_yaml
