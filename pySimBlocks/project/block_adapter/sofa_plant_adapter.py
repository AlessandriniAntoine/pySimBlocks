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

