# pySimBlocks/project/generate_run_script.py

import argparse
from pathlib import Path


RUN_TEMPLATE = """\
from pySimBlocks.core import Model, Simulator
from pySimBlocks.project.load_project_config import load_project_config
from pySimBlocks.project.plot_from_config import plot_from_config

sim_cfg, model_cfg, plot_cfg = load_project_config("{parameters_path}")

model = Model(
    name="model",
    model_yaml="{model_path}",
    model_cfg=model_cfg
)

sim = Simulator(model, sim_cfg)

logs = sim.run()
plot_from_config(logs, plot_cfg)
"""


def generate_run_script(
    *,
    project_dir: Path | None = None,
    model_yaml: Path | None = None,
    parameters_yaml: Path | None = None,
    output: Path | None = None,
) -> None:
    """
    Generate a canonical run.py script for a pySimBlocks project.

    Exactly one of the following modes must be used:
      - project_dir
      - model_yaml + parameters_yaml

    Parameters
    ----------
    project_dir : Path, optional
        Path to a project folder containing model.yaml and parameters.yaml.

    model_yaml : Path, optional
        Path to model.yaml (explicit mode).

    parameters_yaml : Path, optional
        Path to parameters.yaml (explicit mode).

    output : Path, optional
        Output run.py path (default: <project_dir>/run.py).
    """

    # ------------------------------------------------------------
    # Mode validation
    # ------------------------------------------------------------
    explicit_mode = model_yaml is not None or parameters_yaml is not None

    if project_dir and explicit_mode:
        raise ValueError(
            "Cannot use project_dir together with --model/--param."
        )

    if not project_dir and not explicit_mode:
        raise ValueError(
            "You must specify either a project directory or --model and --param."
        )

    # ------------------------------------------------------------
    # Resolve paths
    # ------------------------------------------------------------
    if project_dir:
        project_dir = Path(project_dir)
        model_yaml = project_dir / "model.yaml"
        parameters_yaml = project_dir / "parameters.yaml"
        output = output or (project_dir / "run.py")
    else:
        model_yaml = Path(model_yaml)
        parameters_yaml = Path(parameters_yaml)
        output = Path(output or "run.py")

    if not model_yaml.exists():
        raise FileNotFoundError(f"model.yaml not found: {model_yaml}")

    if not parameters_yaml.exists():
        raise FileNotFoundError(f"parameters.yaml not found: {parameters_yaml}")

    # ------------------------------------------------------------
    # Write run.py
    # ------------------------------------------------------------
    content = RUN_TEMPLATE.format(
        model_path=model_yaml.name,
        parameters_path=parameters_yaml.name,
    )

    output.write_text(content)
    print(f"[pySimBlocks] run script generated: {output}")


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate a canonical run.py for a pySimBlocks project."
    )

    parser.add_argument(
        "folder",
        nargs="?",
        help="Project folder containing model.yaml and parameters.yaml",
    )

    parser.add_argument("--model", help="Path to model.yaml")
    parser.add_argument("--param", help="Path to parameters.yaml")
    parser.add_argument("--out", help="Output run.py path")

    args = parser.parse_args()

    generate_run_script(
        project_dir=Path(args.folder) if args.folder else None,
        model_yaml=Path(args.model) if args.model else None,
        parameters_yaml=Path(args.param) if args.param else None,
        output=Path(args.out) if args.out else None,
    )


if __name__ == "__main__":
    main()
