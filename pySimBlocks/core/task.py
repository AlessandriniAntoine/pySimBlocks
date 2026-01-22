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

class Task:
    """A task represents a group of blocks that share the same sample time."""
    def __init__(self, sample_time, blocks, global_output_order):
        self.sample_time = sample_time
        self.next_activation = 0.0
        self.last_activation = None

        self.output_blocks = [
            b for b in global_output_order
            if b in blocks
        ]
        self.state_blocks = []

    def update_state_blocks(self):
        """Update the list of blocks with state within this task."""
        self.state_blocks = [
            b for b in self.output_blocks
            if b.has_state
        ]

    def should_run(self, t, eps=1e-12):
        """Check if the task should run at time t."""
        return t + eps >= self.next_activation

    def get_dt(self, t):
        """Get the time step for this task at time t."""
        if self.last_activation is None:
            return self.sample_time
        return t - self.last_activation

    def advance(self):
        """Advance the task's activation times."""
        self.last_activation = self.next_activation
        self.next_activation += self.sample_time
