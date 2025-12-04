import streamlit as st
import numpy as np
import types
import os

def render_workspace():
    ws = st.session_state["workspace"]

    cmd = st.chat_input("Python command…")

    if cmd:
        project_dir = st.session_state.get("project_dir", None)
        if project_dir:
            old_cwd = os.getcwd()
            os.chdir(project_dir)

        try:
            try:
                result = eval(cmd, {"np": np}, ws)
                st.session_state["last_result"] = result
            except:
                exec(cmd, {"np": np}, ws)
                st.session_state["last_result"] = "OK"
        except Exception as e:
            st.error(str(e))
        finally:
            if project_dir:
                os.chdir(old_cwd)

    # Display result
    if "last_result" in st.session_state:
        st.write("**Result:**")
        st.write(st.session_state["last_result"])

    st.markdown("---")
    st.write("### Workspace variables")

    for k, v in ws.items():
        if k.startswith("_"):
            continue
        if isinstance(v, (types.ModuleType, types.FunctionType, type)):
            continue
        if k == "np":
            continue
        st.write(f"**{k}** = {v}")
