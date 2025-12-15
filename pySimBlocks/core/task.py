class Task:
    def __init__(self, Ts: float, blocks, global_output_order):
        self.Ts = Ts
        self.next_activation = 0.0

        self.output_blocks = [
            b for b in global_output_order
            if b in blocks
        ]

        self.state_blocks = [
            b for b in self.output_blocks
            if b.has_state
        ]

    def should_run(self, t, eps=1e-12):
        return t + eps >= self.next_activation

    def advance(self):
        self.next_activation += self.Ts
