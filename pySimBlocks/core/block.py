from abc import ABC, abstractmethod
import numpy as np


class Block(ABC):
    """
    Base class for all discrete-time blocks (Simulink-like).

    A block follows two-phase execution:

    1) output_update(t, dt):
           Computes outputs y[k] from:
                - current state x[k]
                - current inputs u[k]

    2) state_update(t, dt):
           Computes next state x[k+1] from:
                - current state x[k]
                - current inputs u[k]
    """

    direct_feedthrough = True
    is_source = False

    def __init__(self, name: str, sample_time: float | None = None):
        self.name = name

        if sample_time is not None and sample_time <= 0:
            raise ValueError(f"[{self.name}] sample_time must be > 0.")
        self.sample_time = sample_time

        # Dict[str -> np.ndarray]
        self.inputs = {}    # ports set by the simulator
        self.outputs = {}   # ports produced at each step

        # Internal states:
        # state: x[k]       (committed state)
        # next_state: x[k+1] (to commit at end of step)
        self.state = {}
        self.next_state = {}

        self._effective_sample_time = 0.

    @property
    def has_state(self):
        """Specify if block is stateful."""
        return bool(self.state) or bool(self.next_state)

    @abstractmethod
    def initialize(self, t0: float):
        """
        Initialize internal state x[0] and outputs y[0].
        Must fill:
            - self.state[...]        (initial state)
            - self.outputs[...]      (initial outputs)
        """

    @abstractmethod
    def output_update(self, t: float, dt: float):
        """
        Compute outputs y[k] from x[k] and inputs u[k].
        Called before state_update.
        Must write to self.outputs[...].
        """

    @abstractmethod
    def state_update(self, t: float, dt: float):
        """
        Compute next state x[k+1] from x[k] and inputs u[k].
        Must write to self.next_state[...].
        """

    def commit_state(self):
        """
        Finalize the step by copying x[k+1] into x[k].
        Called by the simulator after all blocks completed state_update().
        """
        for key, value in self.next_state.items():
            self.state[key] = np.copy(value)

    def finalize(self):
        """
        Optional cleanup method called at the end of the simulation.
        """
