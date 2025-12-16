import streamlit as st

def render_plots_definition(plots, signals_logged):

    st.header("Plots Definition")

    # EDIT
    if st.session_state["edit_plot_index"] is not None:
        idx = st.session_state["edit_plot_index"]
        p = plots[idx]

        title = st.text_input("Title", p["title"])
        sigs = st.multiselect("Signals", signals_logged, default=p["signals"])

        if st.button("Save plot"):
            plots[idx] = {"title": title, "signals": sigs}
            st.session_state["edit_plot_index"] = None
            st.rerun()

        if st.button("Cancel"):
            st.session_state["edit_plot_index"] = None
            st.rerun()

    # ADD
    else:
        # Clear after an Add
        if st.session_state.get("clear_plot_form", False):
            st.session_state["new_plot_title"] = ""
            st.session_state["new_plot_signals"] = []
            st.session_state["clear_plot_form"] = False

        title = st.text_input("New plot title", key="new_plot_title")
        sigs  = st.multiselect("Signals", signals_logged, key="new_plot_signals")

        if st.button("Add plot"):
            if title and sigs:
                plots.append({"title": title, "signals": sigs})
                st.session_state["clear_plot_form"] = True
                st.rerun()


    with st.expander("Existing plots"):
        for i, p in enumerate(plots):
            cols = st.columns([4,1,1])
            cols[0].write(f"{p['title']} – {p['signals']}")
            if cols[1].button("Edit", key=f"edit_plot_{i}"):
                st.session_state["edit_plot_index"] = i
                st.rerun()
            if cols[2].button("Delete", key=f"del_plot_{i}"):
                plots.pop(i)
                st.rerun()

    return signals_logged
