import streamlit as st
from typing import Dict

from pySimBlocks.tools.blocks_registry import BlockMeta
from pySimBlocks.gui.helpers import parse_yaml_value


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def _param_is_visible(pname, pmeta: dict, values: dict) -> bool:
    depends_on = pmeta.get("depends_on")
    if not depends_on:
        return True

    dep_param = depends_on.get("parameter")
    allowed_values = depends_on.get("values", [])

    if dep_param is None:
        return True  # malformed metadata → be permissive

    current_value = values.get(dep_param)

    if current_value is None:
        return False

    return current_value in allowed_values




# ---------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------
def _param_default_as_str(pmeta: dict) -> str:
    default = pmeta.get("default", "")
    required = pmeta.get("required", True)
    autofill = pmeta.get("autofill", False)
    if required or autofill:
        if default is not None:
            return str(default)
    return ""


def _reset_add_block_form(key_prefix, meta, block_type):
    # reset name
    st.session_state[f"{key_prefix}::name"] = block_type

    # reset parameters (AS STRING)
    for pname, pmeta in meta.parameters.items():
        st.session_state[f"{key_prefix}::param::{pname}"] = _param_default_as_str(pmeta)


def _add_block(key_prefix, block_type, block_name, values, model_yaml):
    existing = st.session_state["parameters_yaml"]["blocks"].keys()
    if block_name not in existing:
            unique_name = block_name
    else:
        i = 1
        while f"{block_name}_{i}" in existing:
            i += 1

        unique_name = f"{block_name}_{i}"

    model_yaml = dict(model_yaml)
    model_yaml["name"] = unique_name

    st.session_state["parameters_yaml"]["blocks"][unique_name] = values
    st.session_state["model_yaml"]["blocks"].append(model_yaml)
    st.session_state[f"{key_prefix}::name"] = block_type



def _save_block(edit_index, old_name, new_name, values, model_yaml):
    # update parameters
    params = st.session_state["parameters_yaml"]["blocks"]
    params.pop(old_name)
    params[new_name] = values

    # update model block
    st.session_state["model_yaml"]["blocks"][edit_index] = model_yaml

    # exit edit mode
    st.session_state["edit_block"] = None


def _delete_block(block_index, block_name):
    model_yaml = st.session_state["model_yaml"]
    params_yaml = st.session_state["parameters_yaml"]

    # --------------------------------------------------
    # 1. Remove block from model
    # --------------------------------------------------
    model_yaml["blocks"].pop(block_index)

    # --------------------------------------------------
    # 2. Remove parameters
    # --------------------------------------------------
    params_yaml.get("blocks", {}).pop(block_name, None)

    # --------------------------------------------------
    # 3. Remove related connections
    # --------------------------------------------------
    connections = model_yaml.get("connections", [])
    model_yaml["connections"] = [
        c for c in connections
        if not (
            c[0].startswith(f"{block_name}.")
            or c[1].startswith(f"{block_name}.")
        )
    ]

    # --------------------------------------------------
    # 4. Remove related logged signals
    # --------------------------------------------------
    logged = params_yaml.get("logging", [])
    params_yaml["logging"] = [
        s for s in logged if not s.startswith(f"{block_name}.")
    ]

    # --------------------------------------------------
    # 5. Update plots
    # --------------------------------------------------
    plots = params_yaml.get("plots", [])
    cleaned_plots = []

    for p in plots:
        # remove signals from this block
        new_signals = [
            s for s in p.get("signals", [])
            if not s.startswith(f"{block_name}.")
        ]

        # keep plot only if it still has signals
        if new_signals:
            cleaned_plots.append({
                "title": p["title"],
                "signals": new_signals,
            })

    params_yaml["plots"] = cleaned_plots

    # --------------------------------------------------
    # 6. Exit edit mode if needed
    # --------------------------------------------------
    edit_ctx = st.session_state.get("edit_block")
    if edit_ctx and edit_ctx.get("name") == block_name:
        st.session_state["edit_block"] = None


# ---------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------
def add_block_editor(registry, categories):
    st.header("Add Block")

    edit_ctx = st.session_state.get("edit_block")
    is_edit = edit_ctx is not None

    if is_edit and edit_ctx.get("load_form", False):
        category = edit_ctx["category"]
        block_type = edit_ctx["type"]
        meta = registry[category][block_type]
        key_prefix = f"addblock::{category}::{block_type}"

        params = st.session_state["parameters_yaml"]["blocks"].get(
            edit_ctx["name"], {}
        )

        # --- LOAD FORM STATE BEFORE WIDGETS ---
        st.session_state[f"{key_prefix}::name"] = edit_ctx["name"]
        for pname, pmeta in meta.parameters.items():
            val = params.get(pname, pmeta.get("default", ""))
            st.session_state[f"{key_prefix}::param::{pname}"] = "" if val is None else str(val)

        # clear flag so it runs only once
        st.session_state["edit_block"]["load_form"] = False


    if not is_edit:
        category = st.selectbox("Category", categories)
        block_types = sorted(registry[category].keys())
        block_type = st.selectbox("Block type", block_types)
    else:
        category = edit_ctx["category"]
        block_type = edit_ctx["type"]
        st.info(f"Editing block: **{edit_ctx['name']}** ({category} / {block_type})")

    meta: BlockMeta = registry[category][block_type]

    if not is_edit:
        key_prefix = f"addblock::{category}::{block_type}"

        if f"{key_prefix}::initialized" not in st.session_state:
            st.session_state[f"{key_prefix}::name"] = block_type

            for pname, pmeta in meta.parameters.items():
                st.session_state[f"{key_prefix}::param::{pname}"] = _param_default_as_str(pmeta)

            st.session_state[f"{key_prefix}::initialized"] = True


    st.markdown(f"**{meta.name}**")
    st.caption(meta.summary)

    if meta.doc_path:
        with st.expander("Block documentation"):
            st.markdown(meta.doc_path.read_text())

    st.divider()
    # ------------------------------------------------------------
    # 3. Block name
    # ------------------------------------------------------------
    key_prefix = f"addblock::{category}::{block_type}"
    default_name = edit_ctx["name"] if is_edit else block_type
    block_name = st.text_input(
        "Block instance name",
        value=default_name,
        key=f"{key_prefix}::name",
    )


    if not block_name:
        st.warning("Block name is required.")
        return

    # ------------------------------------------------------------
    # 4. Parameters
    # ------------------------------------------------------------
    st.subheader("Parameters")
    existing_params = {}
    if is_edit:
        existing_params = st.session_state["parameters_yaml"]["blocks"].get(
            edit_ctx["name"], {}
        )
    values: Dict[str, str] = {}

    # ---- pass 1: enums (needed for dependencies)
    for pname, pmeta in meta.parameters.items():
        default = existing_params.get(pname, pmeta.get("default", ""))
        if pmeta.get("type") == "enum":
            options = pmeta.get("enum", [])

            value = st.selectbox(
                pname,
                options,
                index = options.index(default) if default in options else 0,
                help=pmeta.get("description", ""),
                key=f"{key_prefix}::param::{pname}",
        )
        else:
            if not _param_is_visible(pname, pmeta, values):
                values.pop(pname, None)
                continue

            value = st.text_input(
                pname,
                help=pmeta.get("description", ""),
                key=f"{key_prefix}::param::{pname}",
            )

        if pmeta.get("required", False) and value.strip() == "":
            st.warning(f"Parameter '{pname}' is required.")


        parsed = parse_yaml_value(value)
        if parsed is None:
            values.pop(pname, None)
        else:
            values[pname] = parsed

    # ------------------------------------------------------------
    # 5. Buttons
    # ------------------------------------------------------------
    model_yaml = {
            "name": block_name,
            "category": meta.category,
            "type": meta.type,
        }
    col_main, col_reset = st.columns([3, 1])

    if not is_edit:
        col_main.button(
            "Add block",
            on_click=_add_block,
            args=(key_prefix, block_type, block_name, values, model_yaml),
        )
    else:
        col_main.button(
            "Save block",
            on_click=_save_block,
            args=(
                edit_ctx["index"],
                edit_ctx["name"],
                block_name,
                values,
                model_yaml,
            ),
        )

    col_reset.button(
        "Reset",
        on_click=_reset_add_block_form,
        args=(key_prefix, meta, block_type),
    )



def render_block_list(registry):

    model_yaml = st.session_state.get("model_yaml", {})
    blocks = model_yaml['blocks']
    with st.expander("Existing Blocks"):

        if not blocks:
            st.info("No blocks defined yet.")
            return

        for i, b in enumerate(blocks):
            cols = st.columns([3, 1, 1])

            cols[0].write(f"**{b['name']}** ({b['type']})")
            if cols[1].button("Edit", key=f"edit_block_{i}"):
                st.session_state["edit_block"] = {
                    "index": i,
                    "name": b["name"],
                    "category": b["category"],
                    "type": b["type"],
                    "load_form": True,
                }
                st.rerun()

            if cols[2].button("Delete", key=f"delete_block_{i}"):
                _delete_block(i, b["name"])
                st.rerun()


def render_blocks(registry, categories):
    add_block_editor(registry, categories)
    render_block_list(registry)
