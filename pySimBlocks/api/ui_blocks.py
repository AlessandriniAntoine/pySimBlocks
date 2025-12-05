import streamlit as st
from pySimBlocks.api.utils import parse_array


# ============================================================
# Helpers
# ============================================================
def unique_block_name(name, existing):
    if name not in existing:
        return name
    i = 1
    new = f"{name}_{i}"
    while new in existing:
        i += 1
        new = f"{name}_{i}"
    return new


def clear_param_state(prefix="param_"):
    for key in list(st.session_state.keys()):
        if key.startswith(prefix):
            del st.session_state[key]


# ============================================================
# Existing blocks list
# ============================================================
def render_block_list(blocks):

    with st.expander("Existing Blocks"):

        if not blocks:
            st.info("No blocks defined yet.")
            return

        for i, b in enumerate(blocks):
            cols = st.columns([3, 1, 1])

            cols[0].write(f"**{b['name']}** ({b['type']})")

            if cols[1].button("Edit", key=f"edit_block_{i}"):
                st.session_state["edit_block_index"] = i
                st.rerun()

            if cols[2].button("Delete", key=f"delete_block_{i}"):
                name = b["name"]
                st.session_state["connections"] = [
                    c for c in st.session_state["connections"]
                    if c[0] != name and c[2] != name
                ]
                blocks.pop(i)
                st.rerun()


# ============================================================
# Parameter widget generator
# ============================================================
def render_param_form(block_registry, block_type, filled=None):
    filled = filled or {}
    params = block_registry[block_type]["parameters"]
    values = {}

    for p in params:
        name = p["name"]
        typ  = p["type"]
        default = filled.get(name, "")

        key = f"param_{name}"

        # initialize the entry in session_state
        if key not in st.session_state:
            st.session_state[key] = default

        # Retrieve raw value
        raw = st.session_state.get(key)

        # ALWAYS convert non-string values to string for text widgets
        def ensure_string():
            r = st.session_state[key]
            if not isinstance(r, str):
                r = str(r)
                st.session_state[key] = r
            return r

        # --------------------------------------------------------
        # CASE 1: multiple possible types → text_input only
        # e.g. "float | array | matrix"
        # --------------------------------------------------------
        if "|" in typ:
            raw = ensure_string()
            values[name] = st.text_input(name, value=raw, key=key)
            continue

        # --------------------------------------------------------
        # CASE 2: integer only
        # --------------------------------------------------------
        if typ.strip() == "int":
            try:
                init = int(raw)
            except:
                init = 1
                st.session_state[key] = 1
            values[name] = st.number_input(name, value=init, key=key)
            continue

        # --------------------------------------------------------
        # CASE 3: float only
        # --------------------------------------------------------
        if typ.strip() == "float":
            try:
                init = float(raw)
            except:
                init = 0.0
                st.session_state[key] = 0.0
            values[name] = st.number_input(name, value=init, key=key)
            continue

        # --------------------------------------------------------
        # CASE 4: matrix or array → text_area forced string
        # --------------------------------------------------------
        if typ in ["array", "matrix"]:
            raw = ensure_string()
            values[name] = st.text_area(name, value=raw, key=key)
            continue

        # --------------------------------------------------------
        # DEFAULT: treat as text
        # --------------------------------------------------------
        raw = ensure_string()
        values[name] = st.text_input(name, value=raw, key=key)

    return values


# ============================================================
# Build block instance object
# ============================================================
def compute_block_instance(block_registry, block_type, category, name, params):
    reg = block_registry[block_type]
    ws  = st.session_state["workspace"]

    parsed = {}

    for k, v in params.items():

        # workspace reference
        if isinstance(v, str) and v.strip().startswith("="):
            varname = v.strip()[1:].strip()
            if varname not in ws:
                st.error(f"Workspace variable '{varname}' not found")
                st.stop()
            val = ws[varname]
            if hasattr(val, "tolist"):
                val = val.tolist()
            parsed[k] = val
            continue

        # array or matrix
        if isinstance(v, str) and any(s in v for s in ["[", ",", ";"]):
            parsed[k] = parse_array(v)
            continue

        # numeric auto-detection
        if isinstance(v, str):
            txt = v.strip()
            if txt.isdigit() or (txt.startswith("-") and txt[1:].isdigit()):
                parsed[k] = int(txt)
                continue
            try:
                parsed[k] = float(txt)
                continue
            except:
                pass

        parsed[k] = v

    # Gestion static-dynamic inputs
    reg_in = reg["inputs"]

    if reg_in["dynamic"] == "indexed":
        N = int(parsed["num_inputs"])
        inputs = [reg_in["pattern"].format(i+1) for i in range(N)]

    elif reg_in["dynamic"] == "specified":
        key_param = reg_in["parameter"]
        inputs = parsed[key_param]

    else:  # static
        inputs = reg_in["ports"]

    # Gestion static-dynamic outputs
    reg_out = reg["outputs"]

    if reg_out["dynamic"] == "indexed":
        N = int(parsed["num_outputs"])
        outputs = [reg_out["pattern"].format(i+1) for i in range(N)]

    elif reg_out["dynamic"] == "specified":
        key_param = reg_out["parameter"]
        outputs = parsed[key_param]

    else:
        outputs = reg_out["ports"]

    # name generation
    final_name = name.strip() or block_type
    existing = [b["name"] for b in st.session_state["blocks"]]

    if st.session_state["edit_block_index"] is not None:
        idx = st.session_state["edit_block_index"]
        existing = [nm for j, nm in enumerate(existing) if j != idx]

    final_name = unique_block_name(final_name, existing)

    return {
        "name": final_name,
        "from": category,
        "type": block_type,
        "parameters": parsed,
        "computed_inputs": inputs,
        "computed_outputs": outputs,
    }


# ============================================================
# Main UI section
# ============================================================
def render_block_form(block_registry, categories, blocks):

    st.header("Add / Edit Block")

    # ============================================================
    # EDIT MODE
    # ============================================================
    if st.session_state["edit_block_index"] is not None:
        idx = st.session_state["edit_block_index"]
        blk = blocks[idx]

        st.info(f"Editing block {blk['name']}")

        block_name = st.text_input("Block name", blk["name"])
        category   = blk["from"]
        st.write(f"Category: {category}")

        types = [t for t, v in block_registry.items() if v["category"] == category]
        block_type = st.selectbox("Type", types, index=types.index(blk["type"]))

        params = render_param_form(block_registry, block_type, blk["parameters"])

        if st.button("Save block"):
            blocks[idx] = compute_block_instance(block_registry, block_type, category, block_name, params)
            st.session_state["edit_block_index"] = None
            clear_param_state()
            st.rerun()

        if st.button("Cancel"):
            st.session_state["edit_block_index"] = None
            clear_param_state()
            st.rerun()

        return

    # ============================================================
    # ADD MODE
    # ============================================================

    # ---------- PRE-WIDGET CLEANUP ----------
    if st.session_state.get("clear_block_name_next", False):
        st.session_state["new_block_name"] = ""
        st.session_state["clear_block_name_next"] = False

    if st.session_state.get("clear_params_next", False):
        clear_param_state()
        st.session_state["clear_params_next"] = False

    # ---------- ADD WIDGETS ----------
    block_name = st.text_input("Block name", key="new_block_name")

    category = st.selectbox("Category", categories, key="new_block_category")
    types = [t for t, v in block_registry.items() if v["category"] == category]
    block_type = st.selectbox("Type", types, key="new_block_type")

    params = render_param_form(block_registry, block_type)

    col_add, col_reset = st.columns([3,1])

    # ---------- ADD BLOCK ----------
    if col_add.button("Add block"):
        blk = compute_block_instance(block_registry, block_type, category, block_name, params)
        blocks.append(blk)

        st.session_state["clear_block_name_next"] = True
        st.rerun()

    # ---------- RESET ----------
    if col_reset.button("Reset fields"):
        st.session_state["clear_params_next"] = True
        st.session_state["clear_block_name_next"] = True
        st.rerun()
