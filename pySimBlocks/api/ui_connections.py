import streamlit as st

def render_connections(blocks, connections):
    st.header("Connections")

    if blocks:
        names = [b["name"] for b in blocks]

        src = st.selectbox("Source block", names)
        s_blk = next(b for b in blocks if b["name"] == src)
        s_port = st.selectbox("Source port", s_blk["computed_outputs"])

        dst = st.selectbox("Destination block", names)
        d_blk = next(b for b in blocks if b["name"] == dst)
        d_port = st.selectbox("Destination port", d_blk["computed_inputs"])

        if st.button("Connect"):
            connections.append((src, s_port, dst, d_port))
            st.rerun()

    with st.expander("Existing connections"):

        for i, (s, sp, d, dp) in enumerate(connections):
            cols = st.columns([4,1])
            cols[0].write(f"{s}.{sp} → {d}.{dp}")
            if cols[1].button("Delete", key=f"del_conn_{i}"):
                connections.pop(i)
                st.rerun()
