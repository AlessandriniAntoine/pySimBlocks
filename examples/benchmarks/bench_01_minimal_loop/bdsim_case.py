import os
import time
from contextlib import redirect_stdout

import bdsim
import numpy as np
import params as prm

# params

def test_bdsim_case():
    sim = bdsim.BDSim(animation=False, progress=False, verbose=False, toolboxes=False)
    bd = sim.blockdiagram()  # create an empty block diagram

    tuples = [(k * prm.dt, float(prm.noise_sequence[k])) for k in range(prm.N + 2)]
    clock        = bd.clock(prm.dt) 

# define the blocks
    src = bd.PIECEWISE(seq=tuples, name='noise')
    gain_alpha    = bd.GAIN(prm.alpha)
    gain_1malpha = bd.GAIN(1 - prm.alpha)
    sum_block    = bd.SUM('++')
    zoh          = bd.ZOH(clock, x0=prm.x0)

# connect the blocks
    bd.connect(src,          gain_alpha)
    bd.connect(gain_alpha,   sum_block[0])
    bd.connect(gain_1malpha, sum_block[1])
    bd.connect(sum_block,    zoh)        
    bd.connect(zoh,          gain_1malpha)

    bd.compile(report=False, verbose=False)


    t0 = time.perf_counter()
    with redirect_stdout(open(os.devnull, 'w')):
        out = sim.run(bd, T=prm.T, dt=prm.dt)
    t1 = time.perf_counter()

    dt_sim = t1 - t0
    t = out.clock0.t.flatten()  # flatten to 1D array
    x = out.clock0.x.flatten()  # flatten to 1D array

    t = np.hstack(([0], t))
    x = np.hstack(([prm.x0], x))

    return t, prm.noise_sequence[:len(t)], x, dt_sim

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    t, noise_data, output_data, dt_sim = test_bdsim_case()

    print(f"bdsim simulation completed in {dt_sim:.2f} seconds")

    # Plot results
    plt.figure(figsize=(10, 6))
    plt.plot(t, noise_data, "--r", label='Noise', alpha=0.7)
    plt.plot(t, output_data, "--b", label='Output', alpha=0.7)
    plt.title('pySimBlocks Simulation Results')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.show()
