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

from pySimBlocks.core.block import Block
from pySimBlocks.core import signal_bus


class Goto(Block):
    """Publish a signal to the global signal bus under a named tag.

    Goto and From blocks implement a virtual wiring mechanism: a Goto writes
    its input to ``signal_bus._signal_bus[tag]`` each tick, and any From block
    with the same tag reads that value without requiring an explicit connection
    in the model graph.

    The model's topological sort injects a virtual edge from each Goto to every
    From sharing the same tag, ensuring the Goto executes before its consumers
    within the same tick.
    """

    direct_feedthrough = True

    def __init__(self, name: str, tag: str, sample_time: float | None = None):
        """Initialize a Goto block.

        Args:
            name: Unique identifier for this block instance.
            tag: Signal bus tag under which the input value is published.
                Must match the tag of the corresponding From block(s).
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.
        """
        super().__init__(name, sample_time)
        self.tag = tag
        self.inputs["in"] = None

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Publish the current input to the signal bus.

        If no input has been connected yet (None), the bus entry is set to None.

        Args:
            t0: Initial simulation time in seconds.
        """
        signal_bus._signal_bus[self.tag] = self.inputs["in"]

    def output_update(self, t: float, dt: float) -> None:
        """Write the input value to the signal bus under this block's tag.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        signal_bus._signal_bus[self.tag] = self.inputs["in"]

    def state_update(self, t: float, dt: float) -> None:
        """No-op: Goto carries no internal state."""
