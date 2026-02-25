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

import argparse
import sys
from pathlib import Path


def _run_gui(project_dir: str | None) -> None:
    from pySimBlocks.gui.editor import run_app

    path = Path(project_dir).resolve() if project_dir else Path.cwd().resolve()
    run_app(path)


def _run_export(args: argparse.Namespace) -> None:
    project_yaml = Path(args.project_file) if args.project_file else None
    project_dir = Path(args.project_dir) if args.project_dir else Path(".")
    output = Path(args.out) if args.out else None

    if args.sofa_controller:
        from pySimBlocks.project.generate_sofa_controller import generate_sofa_controller

        generate_sofa_controller(project_dir=project_dir, project_yaml=project_yaml)
    else:
        from pySimBlocks.project import generate_run_script

        generate_run_script(project_dir=project_dir, project_yaml=project_yaml, output=output)


def _run_update() -> None:
    from pySimBlocks.tools.generate_blocks_index import generate_blocks_index

    print("Running pySimBlocks index update...")
    generate_blocks_index()
    print("pySimBlocks update complete.")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pysimblocks",
        description=(
            "pySimBlocks command line interface.\n"
            "Default behavior with no subcommand: launch the GUI editor."
        ),
    )

    subparsers = parser.add_subparsers(dest="command")

    gui_parser = subparsers.add_parser("gui", help="Launch the GUI editor.")
    gui_parser.add_argument(
        "project_dir",
        nargs="?",
        help="Project directory to open. Defaults to current directory.",
    )

    export_parser = subparsers.add_parser(
        "export",
        help="Generate run.py or a SOFA controller from project.yaml.",
    )
    source_group = export_parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "-f",
        "--file",
        "--project",
        dest="project_file",
        help="Path to project.yaml",
    )
    source_group.add_argument(
        "-d",
        "--directory",
        dest="project_dir",
        help="Project directory containing project.yaml",
    )
    export_parser.add_argument("-o", "--out", help="Output run.py path")
    export_parser.add_argument(
        "-s",
        "--sofa-controller",
        action="store_true",
        help="Update SOFA controller from project.yaml instead of generating run.py.",
    )

    subparsers.add_parser("update", help="Regenerate pySimBlocks blocks index.")
    return parser


def main(argv: list[str] | None = None) -> None:
    args_list = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()

    if not args_list:
        _run_gui(project_dir=None)
        return

    if args_list[0] not in {"gui", "export", "update", "-h", "--help"}:
        if len(args_list) > 1:
            parser.error(f"unrecognized arguments: {' '.join(args_list[1:])}")
        _run_gui(project_dir=args_list[0])
        return

    args = parser.parse_args(args_list)
    if args.command == "gui":
        _run_gui(project_dir=args.project_dir)
    elif args.command == "export":
        _run_export(args)
    elif args.command == "update":
        _run_update()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
