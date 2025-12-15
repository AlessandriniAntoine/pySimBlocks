import streamlit as st

def is_numeric_literal(txt: str) -> bool:
    """
    Return True if txt is a pure numeric literal (int or float),
    NOT an expression like 1/60 or 2*dt.
    """
    txt = txt.strip()

    # reject obvious expressions
    if any(op in txt for op in ["/", "*", "+"]):
        return False

    try:
        float(txt)
        return True
    except ValueError:
        return False

def render_simulation_settings():
    st.header("Simulation Settings")

    dt_raw = st.text_input(
        "dt",
        value=st.session_state.get("dt_raw", "0.01")
    )
    T_raw = st.text_input(
        "T",
        value=st.session_state.get("T_raw", "2.0")
    )

    st.session_state["dt_raw"] = dt_raw
    st.session_state["T_raw"] = T_raw

    def normalize(expr):
        expr = expr.strip()
        if is_numeric_literal(expr):
            if "." in expr or "e" in expr.lower():
                return float(expr)
            else:
                return int(expr)
        return expr  # keep expression

    dt = normalize(dt_raw)
    T  = normalize(T_raw)

    signals = [
        f"{b['name']}.outputs.{p}"
        for b in st.session_state["blocks"]
        for p in b["computed_outputs"]
    ]

    signals_logged = st.multiselect(
        "Signals to log",
        signals,
        default=st.session_state.get("logs_loaded", [])
    )

    return dt, T, signals_logged
