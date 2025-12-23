class Task:
    def __init__(self, Ts, blocks, global_output_order):
        self.Ts = Ts
        self.next_activation = 0.0
        self.last_activation = None

        self.output_blocks = [
            b for b in global_output_order
            if b in blocks
        ]

    def update_state_blocks(self):
        self.state_blocks = [
            b for b in self.output_blocks
            if b.has_state
        ]

    def should_run(self, t, eps=1e-12):
        return t + eps >= self.next_activation

    def get_dt(self, t):
        if self.last_activation is None:
            return self.Ts
        return t - self.last_activation

    def advance(self):
        self.last_activation = self.next_activation
        self.next_activation += self.Ts
