import streamlit as st
import numpy as np
import matplotlib.pyplot as plt


def render_plot_results():
    if st.session_state.get("simulation_done", False):
        return

    st.header("Results")
    logs = st.session_state.get("simulation_logs")
    if logs is None:
        return

    time = np.array(logs["time"])
    plot_data = st.session_state.get("parameters_yaml", {}).get("plots", [])
    for fig in plot_data:
        with st.expander(fig["title"]):
            fig_handle = plt.figure()

            for var in fig["signals"]:
                data = np.array(logs[var]).reshape(len(time), -1)
                for i in range(data.shape[1]):
                    plt.step(
                        time,
                        data[:, i],
                        where="post",
                        label=f"{var}[{i}]"
                    )

            plt.grid()
            plt.legend()
            st.pyplot(fig_handle)
