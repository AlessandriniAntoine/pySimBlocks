
class FixedStepTimeManager:
    def __init__(self, dt_base: float, sample_times: list[float]):

        if dt_base <= 0:
            raise ValueError("Base time step must be strictly positive.")

        self.dt = dt_base
        self._check_sample_times(sample_times)

    def _check_sample_times(self, sample_times):
        eps = 1e-12
        for Ts in sample_times:
            ratio = Ts / self.dt
            if abs(ratio - round(ratio)) > eps:
                raise ValueError(
                    f"In fixed-step mode, sample_time={Ts} "
                    f"is not a multiple of base dt={self.dt}."
                )

    def next_dt(self, t):
        return self.dt
