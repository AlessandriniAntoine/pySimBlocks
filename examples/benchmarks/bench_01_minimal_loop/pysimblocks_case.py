import time
from pathlib import Path
from pySimBlocks.project import load_simulator_from_project


try:
    BASE_DIR = Path(__file__).parent.resolve()
except Exception:
    BASE_DIR = Path("")

def test_pysimblocks_case():
    sim, plot_cfg = load_simulator_from_project(BASE_DIR / 'project.yaml')

    t0 = time.perf_counter()
    _ = sim.run()
    t1 = time.perf_counter()
    dt_sim = t1 - t0

    t = sim.get_data("time").reshape(-1)
    noise_data = sim.get_data(block="WhiteNoise", port="out").reshape(-1)
    output_data = sim.get_data(block="Delay", port="out").reshape(-1)

    return t, noise_data, output_data, dt_sim

# Plot results
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    t, noise_data, output_data, dt_sim = test_pysimblocks_case()

    print(f"pySimBlocks simulation completed in {dt_sim:.2f} seconds")
    print(noise_data.shape, output_data.shape)

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

