import streamlit as st


def cleanup_logs_and_plots():
    valid_signals = {
        f"{b['name']}.outputs.{p}"
        for b in st.session_state["blocks"]
        for p in b["computed_outputs"]
    }

    # Logs
    if "logs_loaded" in st.session_state:
        st.session_state["logs_loaded"] = [
            s for s in st.session_state["logs_loaded"]
            if s in valid_signals
        ]

    # Plots
    new_plots = []
    for p in st.session_state.get("plots", []):
        sigs = [s for s in p["signals"] if s in valid_signals]
        if sigs:
            new_plots.append({**p, "signals": sigs})
    st.session_state["plots"] = new_plots
