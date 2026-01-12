import importlib.util
from pathlib import Path


def algebraic_function_adapter(
    params: dict,
    parameters_dir: Path,
) -> dict:
    """
    Adapt declarative parameters of AlgebraicFunction
    into executable parameters.

    Expected input:
        {
            "file_path": "...",
            "function_name": "...",
            "input_keys": [...],
            "output_keys": [...],
            "sample_time": ...
        }

    Output:
        {
            "function": callable,
            "input_keys": [...],
            "output_keys": [...],
            "sample_time": ...
        }
    """

    # --------------------------------------------------
    # 1. Validate required fields
    # --------------------------------------------------
    try:
        file_path = params["file_path"]
        func_name = params["function_name"]
    except KeyError as e:
        raise ValueError(
            f"AlgebraicFunction adapter missing parameter: {e}"
        )

    # --------------------------------------------------
    # 2. Resolve file path (RELATIVE TO parameters.yaml)
    # --------------------------------------------------
    path = Path(file_path)
    if not path.is_absolute():
        path = (parameters_dir / path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"Function file not found: {path}")

    # --------------------------------------------------
    # 3. Load module
    # --------------------------------------------------
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    # --------------------------------------------------
    # 4. Extract function
    # --------------------------------------------------
    try:
        func = getattr(module, func_name)
    except AttributeError:
        raise AttributeError(
            f"Function '{func_name}' not found in {path}"
        )

    if not callable(func):
        raise TypeError(
            f"'{func_name}' in {path} is not callable"
        )

    # --------------------------------------------------
    # 5. Build adapted parameter dict
    # --------------------------------------------------
    adapted = dict(params)

    # remove declarative-only keys
    adapted.pop("file_path", None)
    adapted.pop("function_name", None)

    # inject executable function
    adapted["function"] = func

    return adapted

