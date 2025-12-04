import yaml
import streamlit as st
from pySimBlocks.api.utils import FlowStyleList

def render_yaml_export(blocks, connections, dt, T, logs, plots):
    st.header("YAML Export")

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

    yaml_str = yaml.dump(yaml_data, sort_keys=False)
    with st.expander("file content"):
        st.code(yaml_str, language="yaml")

    st.download_button("Download YAML", yaml_str, file_name="model.yaml")

    return yaml_data       # <-- indispensable !
