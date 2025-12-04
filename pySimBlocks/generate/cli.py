import argparse
import yaml
import os

from pySimBlocks.generate.generate_parameters import generate_parameters
from pySimBlocks.generate.generate_model import generate_model
from pySimBlocks.generate.generate_run import generate_run


def generate_project(config_path, out_dir):
    """Generate a full pySimBlocks project from YAML."""

    if out_dir is None or out_dir.strip() == "":
        # default = yaml file basename without extension
        out_dir = os.path.splitext(os.path.basename(config_path))[0]

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    blocks = data.get("blocks", [])
    connections = data.get("connections", [])
    simulation = data.get("simulation", {})
    plots = data.get("plot", [])

    os.makedirs(out_dir, exist_ok=True)

    lines_param = generate_parameters(blocks, simulation)
    lines_model = generate_model(blocks, connections)
    lines_run = generate_run(simulation, plots)

    with open(os.path.join(out_dir, "parameters_auto.py"), "w") as f:
        f.write("\n".join(lines_param))

    with open(os.path.join(out_dir, "model.py"), "w") as f:
        f.write("\n".join(lines_model))

    with open(os.path.join(out_dir, "run.py"), "w") as f:
        f.write("\n".join(lines_run))

    print(f"[pySimBlocks] Project generated in: {out_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a pySimBlocks Python project from a YAML configuration."
    )

    # NEW: config file is now a **positional argument**
    parser.add_argument(
        "config",
        help="YAML configuration file for pySimBlocks."
    )

    # NEW: optional --out argument
    parser.add_argument(
        "--out",
        default=None,
        help="Output directory (default = base name of YAML file)."
    )

    args = parser.parse_args()

    generate_project(args.config, args.out)
