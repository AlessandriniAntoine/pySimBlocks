import yaml
import streamlit as st


def render_generated_code():
    yaml_data = st.session_state.get("yaml_data", None)

    yaml_str = yaml.dump(yaml_data, sort_keys=False)
    param = st.session_state["generated_param"]
    model = st.session_state["generated_model"]
    run = st.session_state["generated_run"]

    st.markdown("---")
    st.header("Generated Files")

    with st.expander("project.yaml"):
        st.code(yaml_str, language="yaml")

    with st.expander("parameters_auto.py"):
        st.code(param, language="python")

    with st.expander("model.py"):
        st.code(model, language="python")

    with st.expander("run.py"):
        st.code(run, language="python")
