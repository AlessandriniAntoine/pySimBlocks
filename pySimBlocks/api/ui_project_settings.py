import streamlit as st
import yaml
import uuid

from pySimBlocks.api.cleanup_logs_plot import cleanup_logs_and_plots

def render_project_settings(registry):
    st.header("Project Settings")

    with st.expander("Project folder"):
        folder = st.text_input("Project directory", st.session_state["project_dir"] or "")
        if st.button("Set directory"):
            if folder:
                st.session_state["project_dir"] = folder
                st.success(f"Project directory set to: {folder}")
                st.rerun()

    with st.expander("Load project.py"):
        render_load_yaml(registry)


def render_load_yaml(registry):
    """
    Load a YAML project into session_state.
    Uses a two-step rerun AND resets the file_uploader
    to avoid infinite rerun loops.
    """

    # ============================================================
    # 1) If a YAML load is pending (after rerun)
    # ============================================================
    if "pending_yaml" in st.session_state:
        data = st.session_state["pending_yaml"]
        del st.session_state["pending_yaml"]

        try:
            # Reset all data
            st.session_state["blocks"] = []
            st.session_state["connections"] = []
            st.session_state["plots"] = []
            st.session_state["edit_block_index"] = None
            st.session_state["edit_plot_index"] = None

            # Load blocks
            for blk in data.get("blocks", []):
                blk_type = blk["type"]
                blk_cat  = blk["from"]
                params = {k: v for k, v in blk.items()
                          if k not in ["name", "type", "from"]}

                ### --- Compute INPUT PORTS ---
                reg_in = registry[blk_type]["inputs"]

                dynamic_mode = reg_in.get("dynamic", False)

                if dynamic_mode == "indexed":
                    # EX: in1, in2, ..., inN
                    N = int(params.get("num_inputs", 1))
                    computed_inputs = [reg_in["pattern"].format(i+1) for i in range(N)]

                elif dynamic_mode == "specified":
                    # EX: input_keys = ["cable", "motor"]
                    param_name = reg_in["parameter"]  # ex: "input_keys"
                    if param_name not in params:
                        raise RuntimeError(f"Missing required parameter '{param_name}' for block {blk['name']}")
                    computed_inputs = params[param_name]

                else:
                    # STATIC PORTS
                    computed_inputs = reg_in.get("ports", [])


                ### --- Compute OUTPUT PORTS ---
                reg_out = registry[blk_type]["outputs"]
                dynamic_mode_out = reg_out.get("dynamic", False)

                if dynamic_mode_out == "indexed":
                    N = int(params.get("num_outputs", 1))
                    computed_outputs = [reg_out["pattern"].format(i+1) for i in range(N)]

                elif dynamic_mode_out == "specified":
                    param_name = reg_out["parameter"]
                    if param_name not in params:
                        raise RuntimeError(f"Missing required parameter '{param_name}' for outputs of block {blk['name']}")
                    computed_outputs = params[param_name]

                else:
                    computed_outputs = reg_out.get("ports", [])


                st.session_state["blocks"].append({
                    "name": blk["name"],
                    "from": blk_cat,
                    "type": blk_type,
                    "parameters": params,
                    "computed_inputs": computed_inputs,
                    "computed_outputs": computed_outputs,
                })

            # Load connections
            for c in data.get("connections", []):
                src, dst = c
                s_b, s_p = src.split(".")
                d_b, d_p = dst.split(".")
                st.session_state["connections"].append((s_b, s_p, d_b, d_p))

            # Load simulation parameters
            sim = data.get("simulation", {})
            st.session_state["dt_raw"] = str(sim.get("dt", "0.01"))
            st.session_state["T_raw"]  = str(sim.get("T", "2.0"))
            st.session_state["logs_loaded"] = sim.get("log", [])

            # Load plots
            st.session_state["plots"] = [
                {"title": p["title"], "signals": p["log"]}
                for p in data.get("plot", [])
            ]

            st.success("YAML project loaded successfully.")

        except Exception as e:
            st.error(f"Error loading YAML: {e}")

        # CRITICAL: regen file_uploader key so it resets
        st.session_state["yaml_uploader_key"] = str(uuid.uuid4())

        cleanup_logs_and_plots()
        st.rerun()
        return True

    # ============================================================
    # 2) First step: user uploads a file (no rerun yet)
    # ============================================================

    # If missing, create a stable but replaceable key
    if "yaml_uploader_key" not in st.session_state:
        st.session_state["yaml_uploader_key"] = "yaml_loader_initial"

    uploaded = st.file_uploader(
        "Load YAML project",
        type=["yaml", "yml"],
        key=st.session_state["yaml_uploader_key"]
    )

    if uploaded is not None:
        try:
            data = yaml.safe_load(uploaded.read())

            # store for next rerun
            st.session_state["pending_yaml"] = data

            # force rerun
            cleanup_logs_and_plots()
            st.rerun()

        except Exception as e:
            st.error(f"Invalid YAML file: {e}")

    return False
