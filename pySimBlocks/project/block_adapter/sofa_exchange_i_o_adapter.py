from pathlib import Path

def sofa_exchange_i_o_adapter(params, parameters_dir):
    adapted = dict(params)
    adapted.pop("scene_file", None)
    return adapted

