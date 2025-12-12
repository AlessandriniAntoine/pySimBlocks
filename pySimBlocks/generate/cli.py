import argparse
import yaml
import os

from pySimBlocks.generate.generate_parameters import generate_parameters
from pySimBlocks.generate.generate_model import generate_model
from pySimBlocks.generate.generate_run import generate_run
from pySimBlocks.generate.generate_sofa_controller import generate_sofa_controller


def process_yaml(config_path):
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    blocks = data.get("blocks", [])
    connections = data.get("connections", [])
    simulation = data.get("simulation", {})
    plots = data.get("plot", [])

    return blocks, connections, simulation, plots


def generate_project(blocks, connections, simulation, plots, config_path, out_dir):
    """Generate a full pySimBlocks project from YAML."""

    if out_dir is None or out_dir.strip() == "":
        # default = yaml file basename without extension
        out_dir = os.path.splitext(os.path.basename(config_path))[0]


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

    parser.add_argument(
        "config",
        help="YAML configuration file for pySimBlocks."
    )

    parser.add_argument(
        "--out",
        default=None,
        help="Output directory (default = base name of YAML file)."
    )


    parser.add_argument(
        "--sofa",
        default=None,
        help="Path to sofa controller to update with pysimblocks. Will be overwritten if nothing specify."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print changes without modifying files."
    )
    args = parser.parse_args()

    blocks, connections, simulation, plots = process_yaml(args.config)

    if args.sofa is None:
        generate_project(blocks, connections, simulation, plots, args.config, args.out)
    else:
        generate_sofa_controller(blocks, connections, simulation, args.sofa, args.dry_run)
