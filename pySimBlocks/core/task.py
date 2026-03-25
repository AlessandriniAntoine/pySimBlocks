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

from typing import List

from pySimBlocks.core.block import Block


class Task:
    """A group of blocks sharing the same sample time.
 
    Manages the scheduling and execution of output updates, state updates,
    and state commits for all blocks in the group.
 
    Scheduling is tick-based: the task maintains an integer countdown reset
    to ``period_ticks - 1`` after each activation. This avoids floating-point
    time comparisons and works correctly with both fixed and external clocks.

    Attributes:
        sample_time: Sampling period of this task in seconds.
        period_ticks: Number of base ticks between two activations.
        ticks_until_next: Countdown to the next activation.
        accumulated_dt: Accumulated time since the last activation.
        output_blocks: Blocks ordered for output computation, filtered from
            the global output order.
        state_blocks: Subset of output_blocks that carry internal state.
    """

    def __init__(
        self,
        sample_time: float,
        period_ticks: int,
        blocks: List[Block],
        global_output_order: List[Block],
    ):
        """Initialize a task.
 
        Args:
            sample_time: Sampling period in seconds.
            blocks: Set of blocks belonging to this task.
            global_output_order: Global topological order of all blocks,
                used to filter and preserve execution order within the task.
        """
        self.sample_time = sample_time
        self.period_ticks = period_ticks
        self.ticks_until_next = 0
        self.accumulated_dt: float = 0.0

        self.output_blocks = [b for b in global_output_order if b in blocks]
        self.state_blocks = []


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
 
    def update_state_blocks(self) -> None:
        """Refresh the list of stateful blocks from output_blocks."""
        self.state_blocks = [b for b in self.output_blocks if b.has_state]

    def should_run(self) -> bool:
        """Return True if the task is due to run at time t.
 
        Returns:
            True if ticks_until_next is zero, indicating that the task should run at the current time step.
        """
        return self.ticks_until_next == 0

    def advance(self) -> None:
        """Advance the countdown by one tick."""
        if self.ticks_until_next == 0:
            self.ticks_until_next = self.period_ticks - 1
        else:
            self.ticks_until_next -= 1

    def accumulate(self, dt: float) -> None:
        """Accumulate the time step dt since the last activation.

        Args:
            dt: Time step in seconds to accumulate.
        """
        self.accumulated_dt += dt

    def reset_accumulated_dt(self) -> None:
        """Reset the accumulated time to zero after an activation."""
        self.accumulated_dt = 0.0
