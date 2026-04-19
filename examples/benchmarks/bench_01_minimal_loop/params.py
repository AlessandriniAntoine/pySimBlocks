import numpy as np

dt = 0.1
N = 100_000
T = N * dt
alpha = 0.1

# noise
std = 1.
seed = 0
rng = np.random.default_rng(seed)
noise_sequence = rng.standard_normal(N + 2)
np.save("noise_seq.npy", noise_sequence)
x0 = 0.
