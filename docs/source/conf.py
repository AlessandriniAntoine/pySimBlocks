from __future__ import annotations

import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "_ext")))

if "Sofa" not in sys.modules:
    sofa = types.ModuleType("Sofa")
    sofa_core = types.ModuleType("Sofa.Core")
    sofa_simulation = types.ModuleType("Sofa.Simulation")
    sofa_imgui = types.ModuleType("Sofa.ImGui")

    class _SofaController:
        def __init__(self, *args, **kwargs):
            pass

    class _SofaNode:
        def __init__(self, *args, **kwargs):
            pass

    def _noop(*args, **kwargs):
        return None

    sofa_core.Controller = _SofaController
    sofa_core.Node = _SofaNode
    sofa_simulation.initRoot = _noop
    sofa_simulation.animate = _noop

    sofa.Core = sofa_core
    sofa.Simulation = sofa_simulation
    sofa.ImGui = sofa_imgui

    sys.modules["Sofa"] = sofa
    sys.modules["Sofa.Core"] = sofa_core
    sys.modules["Sofa.Simulation"] = sofa_simulation
    sys.modules["Sofa.ImGui"] = sofa_imgui

project = "pySimBlocks"
author = "Antoine Alessandrini"
copyright = "2026, Universite de Lille & INRIA"
release = "0.1.1"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
myst_enable_extensions = [
    "dollarmath",
    "colon_fence",
]

autosummary_generate = True
autosummary_imported_members = False
autosummary_ignore_module_all = False

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}

autodoc_member_order = "bysource"
autodoc_mock_imports = []
autodoc_type_aliases = {
    "ArrayLike": "ArrayLike",
}

html_theme = "furo"
html_title = "pySimBlocks Documentation"
html_static_path = ["_static"]
html_css_files = ["custom.css"]


def setup(app):
    from api_generator import generate_api

    app.connect("builder-inited", generate_api)
