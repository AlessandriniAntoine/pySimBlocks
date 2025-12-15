import streamlit as st
import yaml
import os
from pySimBlocks.api.codegen import generate_python_content
from pySimBlocks.generate.generate_sofa_controller import generate_sofa_controller


def project_export(yaml_data, export_mode):
    project_dir = st.session_state.get("project_dir", None)
    if not project_dir:
        st.error("Please set a project directory first.")
        return

    os.makedirs(project_dir, exist_ok=True)
    save_yaml_content(yaml_data, verbose=False)

    # détecter blocs sofa
    sofa_blocks = [b for b in yaml_data["blocks"]
                   if b["type"].lower() in ("sofa_plant", "sofa_exchange_i_o")]

    # ======================================================================
    # CASE 1 — No Sofa block
    # ======================================================================
    if not sofa_blocks or export_mode=="cli-only":
        pySimBloc_export(yaml_data)
        return

    sofa_block = sofa_blocks[0]

    # ======================================================================
    # CASE 2 — SofaExchangeIO → only controller
    # ======================================================================
    if sofa_block["type"].lower() == "sofa_exchange_i_o" or export_mode=="controller-only":
        if len(sofa_blocks) != 1:
            st.error("Cannot have more than one Sofa System for controller generation.")
            return
        else:

            # puis génération controller
            generate_sofa_controller(
                yaml_data["blocks"],
                yaml_data["connections"],
                yaml_data.get("simulation", {}),
            )

            st.success(f"Exported YAML + Sofa controller to {project_dir}")
            return

    # ======================================================================
    # CAS 3 — SofaPlant → command line + controller
    # ======================================================================
    pySimBloc_export(yaml_data)
    generate_sofa_controller(
        yaml_data["blocks"],
        yaml_data["connections"],
        yaml_data.get("simulation", {}),
    )

    st.success(f"Exported SofaPlant project + controller to {project_dir}")


def pySimBloc_export(yaml_data):

    project_dir = st.session_state.get("project_dir", None)
    if not project_dir:
        st.error("Please set a project directory first.")
        return

    generate_python_content(yaml_data)
    param_str = st.session_state["generated_param"]
    model_str = st.session_state["generated_model"]
    run_str = st.session_state["generated_run"]

    os.makedirs(project_dir, exist_ok=True)

    with open(os.path.join(project_dir, "parameters_auto.py"), "w") as f:
        f.write(param_str)

    with open(os.path.join(project_dir, "model.py"), "w") as f:
        f.write(model_str)

    with open(os.path.join(project_dir, "run.py"), "w") as f:
        f.write(run_str)



def save_yaml_content(yaml_data, verbose=True):
    project_dir = st.session_state.get("project_dir", None)
    if not project_dir:
        st.error("Please set a project directory first.")
        return

    os.makedirs(project_dir, exist_ok=True)

    with open(os.path.join(project_dir, "project.yaml"), "w") as f:
        f.write(yaml.dump(yaml_data, sort_keys=False))

    if verbose:
        st.success(f"Exported to {project_dir}")
