from parameters_auto import *
from pySimBlocks import Model, Simulator
from pySimBlocks.blocks.operators.dead_zone import DeadZone
from pySimBlocks.blocks.operators.rate_limiter import RateLimiter
from pySimBlocks.blocks.sources.ramp import Ramp
from pySimBlocks.blocks.sources.sinusoidal import Sinusoidal

model = Model('auto_model')

ramp = Ramp('ramp', slope=ramp_slope, start_time=ramp_start_time, offset=ramp_offset)
model.add_block(ramp)

rate_limiter = RateLimiter('rate_limiter', rising_slope=rate_limiter_rising_slope, falling_slope=rate_limiter_falling_slope, initial_output=rate_limiter_initial_output)
model.add_block(rate_limiter)

dead_zone = DeadZone('dead_zone', lower_bound=dead_zone_lower_bound, upper_bound=dead_zone_upper_bound)
model.add_block(dead_zone)

sinusoidal = Sinusoidal('sinusoidal', amplitude=sinusoidal_amplitude, frequency=sinusoidal_frequency)
model.add_block(sinusoidal)

model.connect('ramp', 'out', 'rate_limiter', 'in')
model.connect('sinusoidal', 'out', 'dead_zone', 'in')

simulator = Simulator(model, dt=dt)