from pathlib import Path
import numpy as np
import scipy.io as sio

dt = 0.001
N = 100_000
T = N * dt
vec_size = 1

seed = 0
rng = np.random.default_rng(seed)
noise_sequence = rng.standard_normal((N + 2, vec_size))
dir_path = Path(__file__).parent
np.save(dir_path / "noise_seq.npy", noise_sequence)

x0 = np.zeros((vec_size, 1))

# Sauvegarde .mat
t_vec = np.arange(N + 2) * dt
noise_data_simulink = np.column_stack([t_vec, noise_sequence])

# sio.savemat("matlab/bench_02_simulink.mat", {
#     "dt": dt,
#     "T": T,
#     "x0": x0,
#     "noise_data": noise_data_simulink,
# })
