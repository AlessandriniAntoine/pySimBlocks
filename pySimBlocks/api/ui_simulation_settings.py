import numpy as np
from fractions import Fraction
import streamlit as st


def parse_value(expr):
    expr = expr.strip()

    try:
        return float(Fraction(expr))
    except Exception:
        pass
    try:
        return float(eval(expr, {"__builtins__": {}}, {"np": np}))
    except Exception:
        st.error(f"Cannot parse value: {expr}")
        return None

def render_simulation_settings():
    st.header("Simulation Settings")
    dt_raw = st.text_input("dt", value=st.session_state.get("dt_raw", "0.01"))
    T_raw  = st.text_input("T",  value=st.session_state.get("T_raw", "2.0"))
    dt = parse_value(dt_raw)
    T = parse_value(T_raw)
    return dt, T
