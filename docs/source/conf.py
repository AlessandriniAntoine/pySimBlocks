from __future__ import annotations

import os
import sys
import types
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

sys.modules["qpsolvers"] = MagicMock()

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
autodoc_mock_imports = ["qpsolvers"]
autodoc_type_aliases = {
    "ArrayLike": "ArrayLike",
}

html_theme = "furo"
html_title = "pySimBlocks Documentation"
html_static_path = ["_static"]
html_css_files = ["custom.css"]


def generate_tutorial_archives(app):
    source_dir = Path(__file__).resolve().parent
    tutorials_root = Path(ROOT) / "examples" / "tutorials"
    archive_dir = source_dir / "_static" / "downloads"
    archive_dir.mkdir(parents=True, exist_ok=True)

    tutorial_dir = tutorials_root / "tutorial_3_sofa"
    archive_path = archive_dir / "tutorial_3_sofa.zip"

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(tutorial_dir.rglob("*")):
            if not file_path.is_file():
                continue
            if "__pycache__" in file_path.parts or file_path.suffix == ".pyc":
                continue
            archive_name = Path("tutorial_3_sofa") / file_path.relative_to(tutorial_dir)
            archive.write(file_path, archive_name.as_posix())


def setup(app):
    from api_generator import generate_api

    app.connect("builder-inited", generate_api)
    app.connect("builder-inited", generate_tutorial_archives)
