from pathlib import Path

def sofa_plant_adapter(params, parameters_dir):
    scene_file = params.get("scene_file")
    if scene_file is None:
        raise ValueError("Missing 'scene_file' parameter")

    path = Path(scene_file)
    if not path.is_absolute():
        path = (parameters_dir / path).resolve()

    adapted = dict(params)
    adapted["scene_file"] = str(path)

    return adapted

