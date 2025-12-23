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
