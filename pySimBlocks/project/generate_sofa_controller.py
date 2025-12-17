import sys
import os
import re
import inspect
from pathlib import Path
from multiprocessing import Process, Pipe
import importlib.util
import yaml

# =============================================================================
#
# =============================================================================
def normalize_block_for_controller(block):
    """
    Force SofaPlant → SofaExchangeIO for controller generation.
    Both share 'input_keys' and 'output_keys'.
    """
    if block["type"].lower() == "sofa_plant":
        return {
            "name": block["name"],
            "type": "sofa_exchange_i_o",
            "from": "systems",
            "input_keys": block["input_keys"],
            "output_keys": block["output_keys"],
        }
    return block



def _load_scene_in_subprocess(scene_path, conn):
    # """
    # Load Sofa Scene in subprocess, get path file from controller.
    # """
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


def detect_controller_file_from_scene(scene_file):
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

    # Cherche la fin du bloc d'import
    import_block = list(re.finditer(r"^(import|from)\s+.+$", src, re.MULTILINE))

    if import_block:
        last = import_block[-1]
        insert_at = last.end()
        return src[:insert_at] + "\n\n" + injection + src[insert_at:]
    else:
        # Aucun import → injecter en tête
        return injection + src

def inject_yaml_paths_into_controller(
    controller_file: Path,
    model_yaml: Path,
    parameters_yaml: Path,
):
    """
    Inject or replace model_yaml and parameters_yaml attributes
    inside the SofaPysimBlocksController __init__.
    """
    src = controller_file.read_text()
    src = inject_base_dir(src)

    def replace_or_add(attr, rel_path):
        expr = (
            f'self.{attr} = str((BASE_DIR / "{rel_path}").resolve())'
        )

        pattern = rf"self\.{attr}\s*=.*"
        if re.search(pattern, src):
            return re.sub(pattern, expr, src)
        else:
            return src.replace(
                "super().__init__(name=name)",
                f"super().__init__(name=name)\n        {expr}"
            )


    controller_dir = controller_file.parent
    rel_model = os.path.relpath(model_yaml, controller_dir)
    rel_param = os.path.relpath(parameters_yaml, controller_dir)

    src = replace_or_add("model_yaml", rel_model)
    src = replace_or_add("parameters_yaml", rel_param)

    controller_file.write_text(src)

# =============================================================================
# MAIN
# =============================================================================
def generate_sofa_controller(
    project_dir: Path | None = None,
    model_yaml: Path | None = None,
    parameters_yaml: Path | None = None,
):
    explicit_mode = model_yaml is not None or parameters_yaml is not None

    if project_dir and explicit_mode:
        raise ValueError(
            "Cannot use project_dir together with --model/--param."
        )

    if not project_dir and not explicit_mode:
        raise ValueError(
            "You must specify either a project directory or --model and --param."
        )


    if explicit_mode:
        if model_yaml is None or parameters_yaml is None:
            raise ValueError(
            "Both --model and --param must be provided together."
        )


    if project_dir:
        project_dir = Path(project_dir).resolve()
        model_yaml = project_dir / "model.yaml"
        parameters_yaml = project_dir / "parameters.yaml"

    if not model_yaml.exists():
        raise FileNotFoundError(model_yaml)
    if not parameters_yaml.exists():
        raise FileNotFoundError(parameters_yaml)

    # 1. Charger model.yaml pour trouver le bloc SOFA
    model_data = yaml.safe_load(model_yaml.read_text())
    params_data = yaml.safe_load(parameters_yaml.read_text())


    blocks = model_data.get("blocks", [])
    sofa_block = next(
        (b for b in blocks if b["type"].lower() in ("sofa_plant", "sofa_exchange_i_o")),
        None
    )
    if sofa_block is None:
        raise RuntimeError("No SofaPlant or SofaExchangeIO block found in model.yaml")

    # 2. Détection automatique du contrôleur depuis la scène
    try:
        scene_file = Path(params_data["blocks"][sofa_block["name"]]["scene_file"])
    except KeyError:
        raise KeyError(
            f"'scene_file' must be defined in parameters.yaml for block '{sofa_block['name']}'"
        )
    controller_file = detect_controller_file_from_scene(scene_file)

    # 3. Injection des chemins YAML
    inject_yaml_paths_into_controller(
        controller_file,
        model_yaml,
        parameters_yaml,
    )

    print(f"[pySimBlocks] SOFA controller updated: {controller_file}")
