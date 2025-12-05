import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import os

def render_run_sim(param_str, model_str, yaml_data):

    st.subheader("Run Simulation")

    if st.button("Run simulation now"):

        project_dir = st.session_state.get("project_dir", None)
        if not project_dir:
            st.error("No project directory set.")
            return

        # Change working directory
        old_cwd = os.getcwd()
        os.chdir(project_dir)

        env = {}
        try:

            # =========================
            # Remove local imports
            # =========================
            model_clean = "\n".join(
                line for line in model_str.splitlines()
                if "from parameters_auto" not in line
            )

            exec(param_str, env, env)
            exec(model_clean, env, env)


            sim = env["sim"]
            T = yaml_data["simulation"]["T"]

            logs = sim.run(T=T, variables_to_log=yaml_data["simulation"].get("log", []))

            st.success("Simulation completed.")

            time = np.arange(0, T, env["dt"])[: len(next(iter(logs.values())))]

            if "plot" in yaml_data:
                st.subheader("Resulted Plots")
                for fig in yaml_data["plot"]:
                    with st.expander(fig["title"]):
                        fig_handle = plt.figure()

                        for var in fig["log"]:
                            data = np.array(logs[var]).reshape(len(time), -1)
                            for i in range(data.shape[1]):
                                plt.step(time, data[:, i], where="post", label=f"{var}[{i}]")

                        plt.grid()
                        plt.legend()
                        st.pyplot(fig_handle)

        except Exception as e:
            st.error(f"Simulation failed: {e}")

        finally:
            os.chdir(old_cwd)
