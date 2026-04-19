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

"""Global signal bus shared by Goto and BusFrom blocks.

Goto blocks write their input value into ``_signal_bus`` under their tag.
BusFrom blocks read from ``_signal_bus`` by tag. The bus is reset at the start
of each simulation run so that successive runs are fully isolated.
"""

_signal_bus: dict = {}


def reset() -> None:
    """Clear all entries in the signal bus.

    Must be called at the start of each simulation run to prevent signal
    bleed-over between independent runs.
    """
    _signal_bus.clear()
