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

class Signal:
    """A lightweight container for a single simulation signal value.

    Used to pass data between blocks through input/output/state ports.
    All block ports (inputs, outputs, state, next_state) hold Signal instances,
    allowing in-place value updates without dict reassignment.

    Attributes:
        value: The current value held by this signal. Can be a scalar float,
            a numpy array, or None if not yet initialized.

    Example:
        >>> s = Signal(0.0)
        >>> s.value
        0.0
        >>> s.value = 3.14
    """
    __slots__ = ("value",)

    def __init__(self, value=None):
        """Initialize a Signal.

        Args:
            value: Initial value for the signal. Defaults to None.
        """
        self.value = value