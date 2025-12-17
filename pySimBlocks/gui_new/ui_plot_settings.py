import streamlit as st


def render_plot_settings():
    st.header("Plots")
    form_action = st.session_state.pop("plot_form_action", None)

    # --------------------------------------------------
    # State
    # --------------------------------------------------
    params_yaml = st.session_state.setdefault("parameters_yaml", {})
    plots = params_yaml.setdefault("plots", [])
    logging = params_yaml.setdefault("logging", [])
    available = st.session_state.get("available_outputs", [])

    edit_ctx = st.session_state.get("edit_plot")
    is_edit = edit_ctx is not None

    # --------------------------------------------------
    # Load plot into form (EDIT mode)
    # --------------------------------------------------
    if is_edit and edit_ctx.get("load_form", False):
        plot = plots[edit_ctx["index"]]
        st.session_state["plot::title"] = plot["title"]
        st.session_state["plot::signals"] = plot["signals"]
        st.session_state["edit_plot"]["load_form"] = False

    # --------------------------------------------------
    # Defaults (ADD mode)
    # --------------------------------------------------
    if not is_edit:
        st.session_state.setdefault("plot::title", "")
        st.session_state.setdefault("plot::signals", [])


    # --------------------------------------------------
    # Handle form actions BEFORE widget creation
    # --------------------------------------------------
    if form_action == "reset":
        st.session_state["plot::title"] = ""
        st.session_state["plot::signals"] = []

    if form_action == "load_edit":
        plot = plots[edit_ctx["index"]]
        st.session_state["plot::title"] = plot["title"]
        st.session_state["plot::signals"] = plot["signals"]

    # --------------------------------------------------
    # Form
    # --------------------------------------------------
    title = st.text_input(
        "Plot title",
        key="plot::title",
    )

    signals = st.multiselect(
        "Signals",
        options=available,
        key="plot::signals",
    )

    # --------------------------------------------------
    # Add / Save
    # --------------------------------------------------
    if not is_edit:
        if st.button("Add plot"):
            if title and signals:
                plots.append(
                    {
                        "title": title,
                        "signals": list(signals),
                    }
                )
                _ensure_logged(signals, logging)
                st.session_state["plot_form_action"] = "reset"
                st.rerun()
    else:
        if st.button("Save plot"):
            idx = edit_ctx["index"]
            plots[idx] = {
                "title": title,
                "signals": list(signals),
            }
            _ensure_logged(signals, logging)
            st.session_state["edit_plot"] = None
            st.session_state["plot_form_action"] = "reset"
            st.rerun()


    # --------------------------------------------------
    # Existing plots
    # --------------------------------------------------
    with st.expander("Existing plots"):
        if not plots:
            st.info("No plots defined.")
            return

        for i, p in enumerate(plots):
            cols = st.columns([4, 1, 1])
            cols[0].write(f"**{p['title']}**  \n{p['signals']}")
            if cols[1].button("Edit", key=f"edit_plot_{i}"):
                st.session_state["edit_plot"] = {
                    "index": i,
                }
                st.session_state["plot_form_action"] = "load_edit"
                st.rerun()
            if cols[2].button("Delete", key=f"del_plot_{i}"):
                plots.pop(i)
                if edit_ctx and edit_ctx["index"] == i:
                    st.session_state["edit_plot"] = None
                st.rerun()


# ===================================================
# Helpers
# ===================================================

def _ensure_logged(signals, logging):
    """
    Ensure that all plotted signals are also logged.
    """
    for s in signals:
        if s not in logging:
            logging.append(s)
