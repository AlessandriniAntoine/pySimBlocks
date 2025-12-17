import streamlit as st
from pySimBlocks.gui.helpers import parse_yaml_value



def render_simulation_settings():
    st.header("Simulation Settings")

    parameters_yaml = st.session_state.get("parameters_yaml", {})
    sim_setting = parameters_yaml.get("simulation", {})
    dt_init = sim_setting.get("dt", 0.1)
    T_init = sim_setting.get("T", 10.)

    dt = st.text_input("dt", value=dt_init)
    T = st.text_input("T sim", value=T_init)

    st.session_state["parameters_yaml"]["simulation"]["dt"] = parse_yaml_value(dt)
    st.session_state["parameters_yaml"]["simulation"]["T"] = parse_yaml_value(T)

    available = st.session_state.get("available_outputs", [])
    signals_logged = st.multiselect(
        "Signals to log",
        available,
        default=st.session_state["parameters_yaml"].get("logging", []),
    )
    st.session_state["parameters_yaml"]["logging"] = signals_logged
