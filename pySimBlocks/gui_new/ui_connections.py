import streamlit as st
from typing import Dict, List

from pySimBlocks.tools.blocks_registry import BlockMeta


# ===============================================================
# Port resolution logic
# ===============================================================

def _resolve_ports_from_def(port_def: dict, params: dict) -> List[str]:
    if not port_def.get("dynamic", False):
        return [port_def.get("pattern", port_def.get("name"))]

    pattern = port_def.get("pattern", "{i}")
    source = port_def.get("source", {})

    if source.get("type") == "parameter":
        pname = source.get("parameter")
        value = params.get(pname)

        # --------------------------------------------------
        # LIST CASE
        # --------------------------------------------------
        if isinstance(value, list):
            # Case A: explicit keys (sofa_plant)
            if "{key}" in pattern:
                return [pattern.format(key=v) for v in value]

            # Case B: list defines number of ports (sum)
            if "{i}" in pattern:
                return [pattern.format(i=i + 1) for i in range(len(value))]

        # --------------------------------------------------
        # INT CASE
        # --------------------------------------------------
        if isinstance(value, int):
            return [pattern.format(i=i + 1) for i in range(value)]

    # --------------------------------------------------
    # FALLBACK (sum.num_inputs)
    # --------------------------------------------------
    fallback = port_def.get("fallback")
    if fallback and fallback.get("type") == "parameter":
        fb_name = fallback.get("parameter")
        fb_value = params.get(fb_name, fallback.get("default"))

        if isinstance(fb_value, int):
            return [pattern.format(i=i + 1) for i in range(fb_value)]

    return []



def compute_block_ports(meta: BlockMeta, params: dict) -> Dict[str, List[str]]:
    """
    Compute effective input/output port names for a block.
    """
    inputs: List[str] = []
    outputs: List[str] = []

    for minput in meta.inputs:
        inputs.extend(_resolve_ports_from_def(minput, params))

    for moutput in meta.outputs:
        outputs.extend(_resolve_ports_from_def(moutput, params))

    return {"inputs": inputs, "outputs": outputs}


def compute_available_outputs(registry) -> list[str]:
    """
    Compute all available output signals based on current model and parameters.
    """
    model_yaml = st.session_state.get("model_yaml", {})
    params_yaml = st.session_state.get("parameters_yaml", {})
    blocks = model_yaml.get("blocks", [])

    outputs = []

    for b in blocks:
        name = b["name"]
        meta = registry[b["category"]][b["type"]]
        params = params_yaml["blocks"].get(name, {})

        ports = compute_block_ports(meta, params)
        for p in ports["outputs"]:
            outputs.append(f"{name}.outputs.{p}")

    return outputs

# ===============================================================
# UI
# ===============================================================
def render_connections(registry):
    st.header("Connections")

    model_yaml = st.session_state.get("model_yaml", {})
    params_yaml = st.session_state.get("parameters_yaml", {})
    blocks = model_yaml.get("blocks", [])
    connections = model_yaml.setdefault("connections", [])

    if not blocks:
        st.info("Define blocks before creating connections.")
        return

    # -----------------------------------------------------------
    # Pre-compute ports for each block
    # -----------------------------------------------------------
    block_ports: Dict[str, Dict[str, List[str]]] = {}

    for b in blocks:
        name = b["name"]
        meta: BlockMeta = registry[b["category"]][b["type"]]
        params = params_yaml["blocks"].get(name, {})

        block_ports[name] = compute_block_ports(meta, params)

    block_names = list(block_ports.keys())

    # -----------------------------------------------------------
    # Connection editor
    # -----------------------------------------------------------
    col_src, col_dst = st.columns(2)

    with col_src:
        src_block = st.selectbox("Source block", block_names)
        src_ports = block_ports[src_block]["outputs"]
        if not src_ports:
            st.warning("This block has no output ports.")
            return
        src_port = st.selectbox("Source port", src_ports)

    with col_dst:
        dst_block = st.selectbox("Destination block", block_names)
        dst_ports = block_ports[dst_block]["inputs"]
        if not dst_ports:
            st.warning("This block has no input ports.")
            return
        dst_port = st.selectbox("Destination port", dst_ports)

    if st.button("Add connection"):
        conn = [f"{src_block}.{src_port}", f"{dst_block}.{dst_port}"]
        if conn not in connections:
            connections.append(conn)
            st.rerun()
        else:
            st.warning("Connection already exists.")

    # -----------------------------------------------------------
    # Existing connections
    # -----------------------------------------------------------
    with st.expander("Existing connections"):
        if not connections:
            st.info("No connections defined.")
            return

        for i, (src, dst) in enumerate(connections):
            cols = st.columns([4, 1])
            cols[0].write(f"{src} → {dst}")
            if cols[1].button("Delete", key=f"del_conn_{i}"):
                connections.pop(i)
                st.rerun()
