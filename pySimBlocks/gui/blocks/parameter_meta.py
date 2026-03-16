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


from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass(frozen=True)
class ParameterMeta:
    """Describe one configurable parameter of a GUI block."""
    
    #: Parameter name.
    name: str
    
    #: User-facing parameter type description.
    type: str
    
    #: Whether the parameter must be provided.
    required: bool = False
    
    #: Whether a default value should be inserted automatically.
    autofill: bool = False
    
    #: Default parameter value.
    default: Optional[Any] = None
     
    #: Allowed values for enum-like parameters.
    enum: List[Any] = field(default_factory=list)
    
    #: Optional help text displayed in the GUI.
    description: str = ""
