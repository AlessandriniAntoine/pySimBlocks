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
from pathlib import Path
from pySimBlocks.project import generate_run_script


def main():
    parser = argparse.ArgumentParser(
        description="Generate a canonical run.py for a pySimBlocks project."
    )

    parser.add_argument(
        "-f",
        "--file",
        "--project",
        dest="project_file",
        help="Path to project.yaml",
    )
    parser.add_argument(
        "-d",
        "--directory",
        dest="project_dir",
        help="Project directory containing project.yaml",
    )
    parser.add_argument(
        "-o",
        "--out",
        help="Output run.py path",
    )
    parser.add_argument(
        "-s",
        "--sofa-controller",
        action="store_true",
        help="Update SOFA controller from project.yaml instead of generating run.py.",
    )

    args = parser.parse_args()

    if args.project_file and args.project_dir:
        parser.error("Use either --file/-f or --directory/-d, not both.")

    project_yaml = None
    project_dir = None

    if args.project_file:
        project_yaml = Path(args.project_file)
    else:
        if args.project_dir:
            project_dir = Path(args.project_dir)
        else:
            project_dir = Path(".")

    if args.sofa_controller:
        from pySimBlocks.project.generate_sofa_controller import generate_sofa_controller
        generate_sofa_controller(
            project_dir=project_dir,
            project_yaml=project_yaml,
        )
    else:
        generate_run_script(
            project_dir=project_dir,
            project_yaml=project_yaml,
            output=Path(args.out) if args.out else None,
        )
