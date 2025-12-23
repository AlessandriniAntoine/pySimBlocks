class FixedStepTimeManager:
    """A time manager for fixed-step simulations.
    Handle multiple sample times by ensuring they are multiples of the base time step.
    """
    def __init__(self, dt_base: float, sample_times: list[float]):

        if dt_base <= 0:
            raise ValueError("Base time step must be strictly positive.")

        self.dt = dt_base
        self._check_sample_times(sample_times)

    def _check_sample_times(self, sample_times):
        """Ensure all sample times are multiples of the base time step."""
        eps = 1e-12
        for st in sample_times:
            ratio = st / self.dt
            if abs(ratio - round(ratio)) > eps:
                raise ValueError(
                    f"In fixed-step mode, sample_time={st} "
                    f"is not a multiple of base dt={self.dt}."
                )

    def next_dt(self, t):
        """Get the next time step (always fixed)."""
        return self.dt
