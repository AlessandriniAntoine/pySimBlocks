import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import os
from pySimBlocks.api.codegen import generate_python_content


def run_simulation(yaml_data):

    project_dir = st.session_state.get("project_dir", None)
    if not project_dir:
        st.error("No project directory set.")
        return

    # Change working directory
    old_cwd = os.getcwd()
    os.chdir(project_dir)

    env = {}
    try:

        generate_python_content(yaml_data)
        param_str = st.session_state["generated_param"]
        model_str = st.session_state["generated_model"]

        # =========================
        # Remove local imports
        # =========================
        model_clean = "\n".join(
            line for line in model_str.splitlines()
            if "from parameters_auto" not in line
        )

        exec(param_str, env, env)
        exec(model_clean, env, env)


        sim = env["simulator"]
        T = yaml_data["simulation"]["T"]

        logs = sim.run(
            T=T,
            variables_to_log=yaml_data["simulation"].get("log", [])
        )

        st.session_state["simulation_logs"] = logs
        st.session_state["simulation_done"] = True
        st.success("Simulation completed.")


    except Exception as e:
        print(f"Failed with {e}")
        st.error(f"Simulation failed: {e}")

    finally:
        os.chdir(old_cwd)
    st.rerun()



def render_results():
    if not st.session_state.get("simulation_done", False):
        return

    yaml_data = st.session_state.get("yaml_data", None)

    logs = st.session_state.get("simulation_logs")
    if logs is None:
        return

    time = np.array(logs["time"])

    st.markdown("---")
    st.header("Results")

    if "plot" in yaml_data:
        for fig in yaml_data["plot"]:
            with st.expander(fig["title"]):
                fig_handle = plt.figure()

                for var in fig["log"]:
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
