import yaml
import streamlit as st
from pySimBlocks.generate.generate_parameters import generate_parameters
from pySimBlocks.generate.generate_model import generate_model
from pySimBlocks.generate.generate_run import generate_run

# ============================================================
# Helpers
# ============================================================
class FlowStyleList(list):
    pass

def flow_representer(dumper, data):
    return dumper.represent_sequence(
        "tag:yaml.org,2002:seq", data, flow_style=True
    )

yaml.add_representer(FlowStyleList, flow_representer)


# ============================================================
# PYTHON
# ============================================================
def generate_python_content(yaml_data):
    blocks = yaml_data["blocks"]
    connections = yaml_data["connections"]
    simulation = yaml_data["simulation"]
    plots = yaml_data.get("plot", [])

    param = "\n".join(generate_parameters(blocks, simulation))
    model = "\n".join(generate_model(blocks, connections))
    run   = "\n".join(generate_run(simulation, plots))

    st.session_state["generated_param"] = param
    st.session_state["generated_model"] = model
    st.session_state["generated_run"]   = run

    st.session_state["generated"] = True

# ============================================================
# YAML
# ============================================================
def generate_yaml_content(blocks, connections, dt, T, logs, plots):
    yaml_blocks = []
    for b in blocks:
        entry = {"name": b["name"], "from": b["from"], "type": b["type"]}

        # Add parameters EXCEPT empty ones
        for k, v in b["parameters"].items():

            # Skip empty strings
            if isinstance(v, str) and v.strip() == "":
                continue

            # Skip None
            if v is None:
                continue

            # If it's a list but empty → skip (optional)
            if isinstance(v, list) and len(v) == 0:
                continue

            # If parsed array (list of lists)
            if isinstance(v, list):
                if isinstance(v[0], list):
                    entry[k] = FlowStyleList([FlowStyleList(row) for row in v])
                else:
                    entry[k] = FlowStyleList(v)
            else:
                entry[k] = v

        yaml_blocks.append(entry)

    yaml_connections = [
        FlowStyleList([f"{s}.{sp}", f"{d}.{dp}"])
        for (s, sp, d, dp) in connections
    ]

    sim = {"dt": dt, "T": T}
    if logs:
        sim["log"] = logs

    yaml_data = {
        "blocks": yaml_blocks,
        "connections": yaml_connections,
        "simulation": sim
    }

    if plots:
        yaml_data["plot"] = [{"title": p["title"], "log": p["signals"]} for p in plots]

    st.session_state["yaml_data"] = yaml_data
