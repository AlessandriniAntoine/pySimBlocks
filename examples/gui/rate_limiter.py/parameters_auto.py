import numpy as np

ramp_slope = np.array([[10.0]])
ramp_start_time = 10
ramp_offset = np.array([[10.0]])

rate_limiter_rising_slope = 7.90634
rate_limiter_falling_slope = -1
rate_limiter_initial_output = np.array([[0.0]])

dead_zone_lower_bound = -0.5
dead_zone_upper_bound = 0.3

sinusoidal_amplitude = 1.0
sinusoidal_frequency = 3.0

dt = 0.016666666666666666
T = 0.5