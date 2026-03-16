from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = ROOT / "docs" / "source"
API_DIR = SOURCE_DIR / "api"
PACKAGE_DIR = ROOT / "pySimBlocks"


SECTIONS = {
    "core": {
        "title": "Core",
        "intro": (
            "The ``core`` package contains the simulation primitives and runtime "
            "orchestration objects."
        ),
        "type": "modules",
        "path": PACKAGE_DIR / "core",
        "generated": "generated/core",
    },
    "project": {
        "title": "Project",
        "intro": (
            "The ``project`` package groups utilities used to load project files, "
            "build simulators, and generate runnable artifacts from project data."
        ),
        "type": "modules",
        "path": PACKAGE_DIR / "project",
        "generated": "generated/project",
    },
    "tools": {
        "title": "Tools",
        "intro": (
            "The ``tools`` package contains support utilities used by the library "
            "and project tooling."
        ),
        "type": "modules",
        "path": PACKAGE_DIR / "tools",
        "generated": "generated/tools",
    },
    "real_time": {
        "title": "Real Time",
        "intro": "The ``real_time`` package provides utilities for live execution workflows.",
        "type": "modules",
        "path": PACKAGE_DIR / "real_time",
        "generated": "generated/real_time",
    },
}


BLOCK_TITLES = {
    "controllers": "Controllers",
    "interfaces": "Interfaces",
    "observers": "Observers",
    "operators": "Operators",
    "optimizers": "Optimizers",
    "sources": "Sources",
    "systems": "Systems",
}


GUI_SECTIONS = {
    "application": {
        "title": "GUI Application",
        "path": PACKAGE_DIR / "gui",
        "modules": [
            "pySimBlocks.gui.editor",
            "pySimBlocks.gui.main_window",
            "pySimBlocks.gui.project_controller",
        ],
        "generated": "generated/gui/application",
    },
    "dialogs": {
        "title": "GUI Dialogs",
        "path": PACKAGE_DIR / "gui" / "dialogs",
        "generated": "generated/gui/dialogs",
    },
    "graphics": {
        "title": "GUI Graphics",
        "path": PACKAGE_DIR / "gui" / "graphics",
        "generated": "generated/gui/graphics",
    },
    "models": {
        "title": "GUI Models",
        "path": PACKAGE_DIR / "gui" / "models",
        "generated": "generated/gui/models",
    },
    "services": {
        "title": "GUI Services",
        "path": PACKAGE_DIR / "gui" / "services",
        "generated": "generated/gui/services",
    },
    "widgets": {
        "title": "GUI Widgets",
        "path": PACKAGE_DIR / "gui" / "widgets",
        "generated": "generated/gui/widgets",
    },
    "addons": {
        "title": "GUI Add-ons",
        "path": PACKAGE_DIR / "gui" / "addons",
        "generated": "generated/gui/addons",
    },
    "block_support": {
        "title": "GUI Block Support",
        "path": PACKAGE_DIR / "gui" / "blocks",
        "modules": [
            "pySimBlocks.gui.blocks.block_dialog_session",
            "pySimBlocks.gui.blocks.block_meta",
            "pySimBlocks.gui.blocks.parameter_meta",
            "pySimBlocks.gui.blocks.port_meta",
        ],
        "generated": "generated/gui/blocks/support",
    },
}


def _title(text: str, underline: str = "=") -> str:
    return f"{text}\n{underline * len(text)}\n\n"


def _discover_modules(path: Path, package: str) -> list[str]:
    modules: list[str] = []
    for py_file in sorted(path.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue
        relative = py_file.relative_to(PACKAGE_DIR).with_suffix("")
        parts = relative.parts
        modules.append("pySimBlocks." + ".".join(parts))
    if package.endswith(".dialogs") or package.endswith(".addons"):
        return modules
    return [m for m in modules if ".__pycache__" not in m]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _generated_doc_path(toctree: str, module: str) -> str:
    return f"{toctree}/{module}.rst"


def _module_page(module: str) -> str:
    title = module
    content = _title(title)
    content += f".. automodule:: {module}\n"
    content += "   :members:\n"
    content += "   :show-inheritance:\n"
    content += "   :member-order: bysource\n"
    content += "\n"
    return content


def _list_page(title: str, intro: str | None, modules: list[str], toctree: str) -> str:
    content = _title(title)
    if intro:
        content += intro + "\n\n"
    content += ".. toctree::\n"
    content += "   :maxdepth: 1\n\n"
    for module in modules:
        generated = f"{toctree}/{module}"
        content += f"   {module} <{generated}>\n"
    content += "\n"
    return content


def _modules_in_dir(path: Path, package: str) -> list[str]:
    return _discover_modules(path, package)


def generate_api(_: object | None = None) -> None:
    _generate_api_index()
    _generate_section_pages()
    _generate_blocks_pages()
    _generate_gui_pages()


def _generate_api_index() -> None:
    content = _title("API Reference")
    content += (
        "The API reference is organized by the package structure of ``pySimBlocks``. "
        "Re-exported symbols from package ``__init__`` files are intentionally not "
        "duplicated here; the canonical documentation lives in the subsection where "
        "each object is implemented.\n\n"
    )
    content += ".. toctree::\n"
    content += "   :maxdepth: 2\n\n"
    for entry in ["blocks/index", "core", "gui/index", "project", "tools", "real_time"]:
        content += f"   {entry}\n"
    content += "\n"
    _write(API_DIR / "index.rst", content)


def _generate_section_pages() -> None:
    for slug, config in SECTIONS.items():
        modules = _modules_in_dir(config["path"], f"pySimBlocks.{slug}")
        content = _list_page(
            config["title"],
            config["intro"],
            modules,
            config["generated"],
        )
        _write(API_DIR / f"{slug}.rst", content)
        for module in modules:
            _write(API_DIR / _generated_doc_path(config["generated"], module), _module_page(module))


def _generate_blocks_pages() -> None:
    blocks_dir = API_DIR / "blocks"
    content = _title("Blocks")
    content += (
        "The ``blocks`` package contains the reusable simulation blocks used to build "
        "models. The reference is split by block family so the runtime implementations "
        "remain easy to browse.\n\n"
    )
    content += ".. toctree::\n   :maxdepth: 1\n\n"
    for category in BLOCK_TITLES:
        content += f"   {category}\n"
    content += "\n"
    _write(blocks_dir / "index.rst", content)

    for category, label in BLOCK_TITLES.items():
        modules = _discover_modules(PACKAGE_DIR / "blocks" / category, f"pySimBlocks.blocks.{category}")
        content = _list_page(
            f"Block {label}",
            None,
            modules,
            f"../generated/blocks/{category}",
        )
        _write(blocks_dir / f"{category}.rst", content)
        for module in modules:
            _write(API_DIR / _generated_doc_path(f"generated/blocks/{category}", module), _module_page(module))


def _generate_gui_pages() -> None:
    gui_dir = API_DIR / "gui"
    content = _title("GUI")
    content += (
        "The ``gui`` package contains the editor application, its support services, "
        "and the GUI-side descriptions used to expose blocks in the interface.\n\n"
    )
    content += ".. toctree::\n   :maxdepth: 1\n\n"
    for entry in ["application", "blocks/index", "dialogs", "graphics", "models", "services", "widgets", "addons"]:
        content += f"   {entry}\n"
    content += "\n"
    _write(gui_dir / "index.rst", content)

    for slug, config in GUI_SECTIONS.items():
        if slug == "block_support":
            continue
        modules = config.get("modules") or _discover_modules(
            config["path"], f"pySimBlocks.gui.{config['path'].relative_to(PACKAGE_DIR / 'gui').as_posix().replace('/', '.')}"
        )
        content = _list_page(config["title"], None, modules, f"../{config['generated']}")
        _write(gui_dir / f"{slug}.rst", content)
        for module in modules:
            _write(API_DIR / _generated_doc_path(config["generated"], module), _module_page(module))

    blocks_dir = gui_dir / "blocks"
    content = _title("GUI Blocks")
    content += (
        "The GUI block metadata is split with the same category structure as the runtime "
        "``blocks`` package, so navigation stays consistent between implementation and "
        "editor-facing code.\n\n"
    )
    content += ".. toctree::\n   :maxdepth: 1\n\n"
    for entry in [*BLOCK_TITLES.keys(), "support"]:
        content += f"   {entry}\n"
    content += "\n"
    _write(blocks_dir / "index.rst", content)

    for category, label in BLOCK_TITLES.items():
        modules = _discover_modules(PACKAGE_DIR / "gui" / "blocks" / category, f"pySimBlocks.gui.blocks.{category}")
        content = _list_page(
            f"GUI Block {label}",
            None,
            modules,
            f"../../generated/gui/blocks/{category}",
        )
        _write(blocks_dir / f"{category}.rst", content)
        for module in modules:
            _write(API_DIR / _generated_doc_path(f"generated/gui/blocks/{category}", module), _module_page(module))

    support_modules = GUI_SECTIONS["block_support"]["modules"]
    content = _list_page(
        "GUI Block Support",
        None,
        support_modules,
        "../../generated/gui/blocks/support",
    )
    _write(blocks_dir / "support.rst", content)
    for module in support_modules:
        _write(API_DIR / _generated_doc_path("generated/gui/blocks/support", module), _module_page(module))
