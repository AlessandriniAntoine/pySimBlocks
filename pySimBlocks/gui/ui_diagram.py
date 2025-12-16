import graphviz as gv
import streamlit as st

def render_diagram(blocks, connections):
    st.header("Diagram")
    dot = gv.Digraph()

    for b in blocks:
        dot.node(
            b["name"],
            f"{b['name']}\n({b['type']})",
            shape="box",
            style="rounded,filled",
            fillcolor="#F0F8FF",
        )

    for (s, sp, d, dp) in connections:
        dot.edge(s, d, label=f"{sp}→{dp}")

    st.graphviz_chart(dot, width='stretch')
