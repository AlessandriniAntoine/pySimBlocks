import streamlit as st
import numpy as np
import sys
import types
import os

def render_workspace():
    st.header("Workspace")

    ws = st.session_state["workspace"]

    cmd = st.chat_input("Python command…")

    if cmd:

        # 1) Ajouter le project_dir dans sys.path
        project_dir = st.session_state.get("project_dir", None)
        if project_dir and project_dir not in sys.path:
            sys.path.insert(0, project_dir)

        # Namespace global persistant
        g = st.session_state.setdefault("workspace_globals", {"np": np})

        try:
            # 2) Essayer exec d'abord (gère les imports)
            try:
                exec(cmd, g, ws)
                result = "OK"
            except SyntaxError:
                # pour les expressions simples
                result = eval(cmd, g, ws)

            # 3) Copier vers le workspace les imports faits dans g
            for k, v in g.items():
                if k not in {"np", "__builtins__"}:
                    ws[k] = v

            st.session_state["last_result"] = result

        except Exception as e:
            st.error(str(e))

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
        st.write(f"**{k}** = {v}")
