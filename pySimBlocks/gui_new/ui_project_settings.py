import streamlit as st


def render_project_settings():
    st.header("Project Settings")

    with st.expander("Project folder"):
        folder = st.text_input("Project directory", st.session_state["project_dir"] or "")
        if st.button("Set directory"):
            if folder:
                st.session_state["project_dir"] = folder
                st.success(f"Project directory set to: {folder}")
                st.rerun()
