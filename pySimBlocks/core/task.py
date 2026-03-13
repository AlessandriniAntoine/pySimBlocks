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
 
    Attributes:
        sample_time: Sampling period of this task in seconds.
        next_activation: Simulation time of the next scheduled execution.
        last_activation: Simulation time of the last execution, or None if
            the task has never run.
        output_blocks: Blocks ordered for output computation, filtered from
            the global output order.
        state_blocks: Subset of output_blocks that carry internal state.
    """

    def __init__(self,
                 sample_time: float,
                 blocks: List[Block],
                 global_output_order: List[Block]):
        """Initialize a task.
 
        Args:
            sample_time: Sampling period in seconds.
            blocks: Set of blocks belonging to this task.
            global_output_order: Global topological order of all blocks,
                used to filter and preserve execution order within the task.
        """
        self.sample_time = sample_time
        self.next_activation = 0.0
        self.last_activation = None

        self.output_blocks = [
            b for b in global_output_order
            if b in blocks
        ]
        self.state_blocks = []

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
 
    def update_state_blocks(self) -> None:
        """Refresh the list of stateful blocks from output_blocks."""
        self.state_blocks = [
            b for b in self.output_blocks
            if b.has_state
        ]

    def should_run(self, t: float, eps: float = 1e-12) -> bool:
        """Return True if the task is due to run at time t.
 
        Args:
            t: Current simulation time in seconds.
            eps: Tolerance for floating-point time comparison.
 
        Returns:
            True if t >= next_activation (within eps).
        """
        return t + eps >= self.next_activation

    def get_dt(self, t: float) -> float:
        """Return the elapsed time since the last activation.
 
        Returns sample_time on the first call (before any activation).
 
        Args:
            t: Current simulation time in seconds.
 
        Returns:
            Elapsed time since last_activation, or sample_time if never run.
        """
        if self.last_activation is None:
            return self.sample_time
        return t - self.last_activation

    def advance(self) -> None:
        """Advance activation timestamps by one sample period."""
        self.last_activation = self.next_activation
        self.next_activation += self.sample_time
