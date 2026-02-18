# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
# ******************************************************************************
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
#  for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ******************************************************************************
#  Authors: see Authors.txt
# ******************************************************************************

import importlib.util
import inspect
import os
import re
import sys
from multiprocessing import Pipe, Process
from pathlib import Path

import yaml


def _load_scene_in_subprocess(scene_path, conn):
    """
    Load SOFA scene in subprocess and return controller file path.
    """
    try:
        scene_path = Path(scene_path).resolve()
        scene_dir = scene_path.parent
        if str(scene_dir) not in sys.path:
            sys.path.insert(0, str(scene_dir))

        spec = importlib.util.spec_from_file_location("scene", scene_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        import Sofa
        root = Sofa.Core.Node("root")

        out = mod.createScene(root)
        if not isinstance(out, (list, tuple)) or len(out) < 2:
            conn.send(None)
            return

        controller = out[1]
        controller_file = inspect.getsourcefile(controller.__class__)
        conn.send(controller_file)

    except Exception as e:
        print(f"Error {e}")
        conn.send(None)

    finally:
        conn.close()


def detect_controller_file_from_scene(scene_file: Path) -> Path:
    """
    Automatically get controller path from scene.
    """
    parent_conn, child_conn = Pipe()
    p = Process(target=_load_scene_in_subprocess, args=(scene_file, child_conn))
    p.start()
    controller_path = parent_conn.recv()
    p.join()

    if controller_path is None:
        raise RuntimeError(
            f"Unable to determine controller file from scene {scene_file}. "
            "Ensure createScene(root) returns (root, controller)."
        )
    return Path(controller_path)


def inject_base_dir(src: str) -> str:
    if "BASE_DIR = Path(__file__).resolve().parent" in src:
        return src

    injection = (
        "from pathlib import Path\n\n"
        "BASE_DIR = Path(__file__).resolve().parent\n\n"
    )

    import_block = list(re.finditer(r"^(import|from)\s+.+$", src, re.MULTILINE))
    if import_block:
        last = import_block[-1]
        insert_at = last.end()
        return src[:insert_at] + "\n\n" + injection + src[insert_at:]

    return injection + src


def inject_project_path_into_controller(
    controller_file: Path,
    project_yaml: Path,
) -> None:
    """
    Inject or replace project_yaml attribute inside SofaPysimBlocksController __init__.
    """
    src = controller_file.read_text()
    src = inject_base_dir(src)

    controller_dir = controller_file.parent
    rel_project = os.path.relpath(project_yaml, controller_dir)
    expr = f'self.project_yaml = str((BASE_DIR / "{rel_project}").resolve())'

    pattern = r"self\.project_yaml\s*=.*"
    if re.search(pattern, src):
        src = re.sub(pattern, expr, src)
    else:
        src = src.replace(
            "super().__init__(name=name)",
            f"super().__init__(name=name)\n        {expr}",
        )

    controller_file.write_text(src)


def _load_project_yaml(project_yaml: Path) -> dict:
    if not project_yaml.exists():
        raise FileNotFoundError(f"project.yaml not found: {project_yaml}")

    raw = yaml.safe_load(project_yaml.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError("project.yaml must define a YAML mapping")
    return raw


def _find_sofa_block(raw_project: dict) -> dict:
    diagram = raw_project.get("diagram", {})
    if not isinstance(diagram, dict):
        raise ValueError("'diagram' section must be a mapping")

    blocks = diagram.get("blocks", [])
    if not isinstance(blocks, list):
        raise ValueError("'diagram.blocks' section must be a list")

    sofa_block = next(
        (
            b
            for b in blocks
            if isinstance(b, dict)
            and str(b.get("type", "")).lower() in ("sofa_plant", "sofa_exchange_i_o")
        ),
        None,
    )
    if sofa_block is None:
        raise RuntimeError(
            "No SofaPlant or SofaExchangeIO block found in project.yaml"
        )
    return sofa_block


def _resolve_scene_file(project_yaml: Path, sofa_block: dict) -> Path:
    params = sofa_block.get("parameters", {})
    if not isinstance(params, dict):
        raise ValueError(
            f"'diagram.blocks[{sofa_block.get('name', '?')}].parameters' must be a mapping"
        )

    scene_file = params.get("scene_file", None)
    if not isinstance(scene_file, str) or not scene_file:
        raise KeyError(
            f"'scene_file' must be defined in parameters for block '{sofa_block.get('name', '?')}'"
        )

    path = Path(scene_file)
    if not path.is_absolute():
        path = (project_yaml.parent / path).resolve()
    return path


def generate_sofa_controller(
    project_dir: Path | None = None,
    project_yaml: Path | None = None,
) -> None:
    has_project_path = project_yaml is not None

    if project_dir and has_project_path:
        raise ValueError("Cannot use project_dir together with project_yaml.")

    if not project_dir and not has_project_path:
        raise ValueError("You must specify either project_dir or project_yaml.")

    if project_dir:
        project_yaml = Path(project_dir).resolve() / "project.yaml"
    else:
        project_yaml = Path(project_yaml).resolve()

    raw_project = _load_project_yaml(project_yaml)
    sofa_block = _find_sofa_block(raw_project)
    scene_file = _resolve_scene_file(project_yaml, sofa_block)
    controller_file = detect_controller_file_from_scene(scene_file)

    inject_project_path_into_controller(controller_file, project_yaml)
    print(f"[pySimBlocks] SOFA controller updated: {controller_file}")
