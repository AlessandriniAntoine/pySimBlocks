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

from pySimBlocks.core.task import Task


class Scheduler:
    """Scheduler for dispatching tasks based on their sample times.

    Attributes:
        tasks: List of tasks sorted by ascending sample time.
    """

    def __init__(self, tasks: list[Task]):
        """Initialize the scheduler.

        Args:
            tasks: List of tasks to schedule.
        """
        self.tasks = sorted(tasks, key=lambda t: t.sample_time)

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def active_tasks(self) -> list[Task]:
        """Return all tasks due to run at the current tick.

        Returns:
            List of tasks whose should_run() returns True.
        """
        return [task for task in self.tasks if task.should_run()]

    def tick(self) -> None:
        """Advance all task countdowns by one tick.

        Must be called once per simulator tick, regardless of which tasks
        were active.
        """
        for task in self.tasks:
            task.advance()
