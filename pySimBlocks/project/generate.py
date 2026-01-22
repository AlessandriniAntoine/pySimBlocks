# ******************************************************************************
#                                 pySimBlocks                                 
#                Copyright (c) 2026 The pySimBlocks Authors               
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
        "folder",
        nargs="?",
        help="Project folder containing model.yaml and parameters.yaml",
    )

    parser.add_argument("--model", help="Path to model.yaml")
    parser.add_argument("--param", help="Path to parameters.yaml")
    parser.add_argument("--out", help="Output run.py path")
    parser.add_argument(
            "--sofa-controller",
            action="store_true",
            help="Path to sofa controller to update with pysimblocks. Will be overwritten if nothing specify."
        )

    args = parser.parse_args()

    if args.sofa_controller:
        from pySimBlocks.project.generate_sofa_controller import generate_sofa_controller
        generate_sofa_controller(
            project_dir=Path(args.folder) if args.folder else None,
            model_yaml=Path(args.model) if args.model else None,
            parameters_yaml=Path(args.param) if args.param else None,
        )
    else:
        generate_run_script(
            project_dir=Path(args.folder) if args.folder else None,
            model_yaml=Path(args.model) if args.model else None,
            parameters_yaml=Path(args.param) if args.param else None,
            output=Path(args.out) if args.out else None,
        )
