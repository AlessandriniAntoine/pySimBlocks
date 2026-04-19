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


class BusFrom(Block):
    """Read a signal from the global signal bus by tag.

    BusFrom and Goto blocks implement a virtual wiring mechanism: a Goto writes
    its input to ``signal_bus._signal_bus[tag]`` each tick, and this block
    reads that value without requiring an explicit connection in the model
    graph.

    The model's topological sort injects a virtual edge from each Goto to every
    BusFrom sharing the same tag, ensuring the Goto executes before this block
    within the same tick.
    """

    direct_feedthrough = True

    def __init__(self, name: str, tag: str, sample_time: float | None = None):
        """Initialize a BusFrom block.

        Args:
            name: Unique identifier for this block instance.
            tag: Signal bus tag to read from. Must match the tag of the
                corresponding Goto block.
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.
        """
        super().__init__(name, sample_time)
        self.tag = tag
        self.outputs["out"] = None

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Read the initial value from the signal bus if available.

        If the tag is not yet in the bus (Goto not yet initialized), the
        output is set to None.

        Args:
            t0: Initial simulation time in seconds.
        """
        self.outputs["out"] = signal_bus._signal_bus.get(self.tag)

    def output_update(self, t: float, dt: float) -> None:
        """Read the current value from the signal bus.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            KeyError: If no Goto with the matching tag has written to the bus
                in this run.
        """
        if self.tag not in signal_bus._signal_bus:
            raise KeyError(
                f"[{self.name}] Tag '{self.tag}' not found in signal bus. "
                "Ensure a Goto block with the same tag exists in the model."
            )
        self.outputs["out"] = signal_bus._signal_bus[self.tag]

    def state_update(self, t: float, dt: float) -> None:
        """No-op: BusFrom carries no internal state."""
