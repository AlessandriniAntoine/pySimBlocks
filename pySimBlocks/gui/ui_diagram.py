import streamlit as st
import graphviz as gv


def render_diagram():
    st.header("Diagram")

    model_yaml = st.session_state.get("model_yaml", {})
    blocks = model_yaml.get("blocks", [])
    connections = model_yaml.get("connections", [])

    if not blocks:
        st.info("No blocks defined.")
        return

    # --------------------------------------------------
    # Create graph
    # --------------------------------------------------
    dot = gv.Digraph(
        graph_attr={
            "splines": "spline",
            "nodesep": "0.6",
            "ranksep": "0.8",
        }
    )

    # --------------------------------------------------
    # Add nodes
    # --------------------------------------------------
    for b in blocks:
        label = f"{b['name']}\n({b['type']})"
        dot.node(
            b["name"],
            label=label,
            shape="box",
            style="rounded,filled",
            fillcolor="#F0F8FF",
        )

    # --------------------------------------------------
    # Add edges
    # --------------------------------------------------
    for conn in connections:
        if len(conn) != 2:
            continue  # safety

        src, dst = conn

        # Expect "block.port"
        try:
            src_block, src_port = src.split(".", 1)
            dst_block, dst_port = dst.split(".", 1)
        except ValueError:
            continue  # malformed connection

        dot.edge(
            src_block,
            dst_block,
            label=f"{src_port} → {dst_port}",
        )

    # --------------------------------------------------
    # Render
    # --------------------------------------------------
    st.graphviz_chart(dot, width='stretch')
