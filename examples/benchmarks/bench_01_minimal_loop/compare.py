import logging

import numpy as np
import matplotlib.pyplot as plt

from bdsim_case import test_bdsim_case
from pathsim_case import test_pathsim_case
from pysimblocks_case import test_pysimblocks_case


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    N_RUNS = 1

    logger.info(f"Running benchmark ({N_RUNS} runs each)...")

    results_bd, results_ps, results_pb = [], [], []
    for i in range(N_RUNS):
        print(f"Run {i+1}/{N_RUNS}...", end="\r")
        results_bd.append(test_bdsim_case())
        results_ps.append(test_pathsim_case())
        results_pb.append(test_pysimblocks_case())

    times_bd = np.array([r[3] for r in results_bd])
    times_ps = np.array([r[3] for r in results_ps])
    times_pb = np.array([r[3] for r in results_pb])

    t_bd, noise_bd, output_bd, _ = results_bd[-1]
    t_ps, noise_ps, output_ps, _ = results_ps[-1]
    t_pb, noise_pb, output_pb, _ = results_pb[-1]

    n = min(len(t_ps), len(t_pb), len(t_bd))
    t_bd, noise_bd, output_bd = t_bd[:n], noise_bd[:n], output_bd[:n]
    t_ps, noise_ps, output_ps = t_ps[:n], noise_ps[:n], output_ps[:n]
    t_pb, noise_pb, output_pb = t_pb[:n], noise_pb[:n], output_pb[:n]
    
    t_error_bd_ps = np.linalg.norm(t_bd - t_ps)
    noise_error_bd_ps = np.linalg.norm(noise_bd - noise_ps)
    output_error_bd_ps = np.linalg.norm(output_bd - output_ps)
    t_error_bd_pb = np.linalg.norm(t_bd - t_pb)
    noise_error_bd_pb = np.linalg.norm(noise_bd - noise_pb)
    output_error_bd_pb = np.linalg.norm(output_bd - output_pb)
    t_error_ps_pb = np.linalg.norm(t_ps - t_pb)
    noise_error_ps_pb = np.linalg.norm(noise_ps - noise_pb)
    output_error_ps_pb = np.linalg.norm(output_ps - output_pb)

    logger.info("")
    logger.info("=== Timing ===")
    logger.info(f"  bdsim:       median={np.median(times_bd)*1e3:.1f} ms,  std={np.std(times_bd)*1e3:.1f} ms")
    logger.info(f"  PathSim:     median={np.median(times_ps)*1e3:.1f} ms,  std={np.std(times_ps)*1e3:.1f} ms")
    logger.info(f"  pySimBlocks: median={np.median(times_pb)*1e3:.1f} ms,  std={np.std(times_pb)*1e3:.1f} ms")
    logger.info(f"  Speedup pySimBlocks vs PathSim: {np.median(times_ps) / np.median(times_pb):.2f}x")
    logger.info(f"  Speedup pySimBlocks vs bdsim:   {np.median(times_bd) / np.median(times_pb):.2f}x")

    logger.info("")
    logger.info("=== Numerical errors (last run) ===")
    logger.info("Librairies | Time error (a/b%) | Noise error (a/b%) | Output error (a/b%)")
    logger.info(f"bdsim vs PathSim | {t_error_bd_ps:.2e} ({t_error_bd_ps / np.linalg.norm(t_ps) * 100:.2f}%) | {noise_error_bd_ps:.2e} ({noise_error_bd_ps / np.linalg.norm(noise_ps) * 100:.2f}%) | {output_error_bd_ps:.2e} ({output_error_bd_ps / np.linalg.norm(output_ps) * 100:.2f}%)")
    logger.info(f"bdsim vs pySimBlocks | {t_error_bd_pb:.2e} ({t_error_bd_pb / np.linalg.norm(t_pb) * 100:.2f}%) | {noise_error_bd_pb:.2e} ({noise_error_bd_pb / np.linalg.norm(noise_pb) * 100:.2f}%) | {output_error_bd_pb:.2e} ({output_error_bd_pb / np.linalg.norm(output_pb) * 100:.2f}%)")
    logger.info(f"PathSim vs pySimBlocks | {t_error_ps_pb:.2e} ({t_error_ps_pb / np.linalg.norm(t_pb) * 100:.2f}%) | {noise_error_ps_pb:.2e} ({noise_error_ps_pb / np.linalg.norm(noise_pb) * 100:.2f}%) | {output_error_ps_pb:.2e} ({output_error_ps_pb / np.linalg.norm(output_pb) * 100:.2f}%)")

    plt.figure(figsize=(10, 6))
    plt.plot(t_bd, noise_bd,  "-.r", label="Noise (bdsim)",     alpha=0.7)
    plt.plot(t_bd, output_bd, "-.b", label="Output (bdsim)",    alpha=0.7)
    plt.plot(t_ps, noise_ps,  "--r", label="Noise (PathSim)",    alpha=0.7)
    plt.plot(t_ps, output_ps, "--b", label="Output (PathSim)",   alpha=0.7)
    plt.plot(t_pb, noise_pb,  ":r",  label="Noise (pySimBlocks)", alpha=0.7)
    plt.plot(t_pb, output_pb, ":b",  label="Output (pySimBlocks)", alpha=0.7)
    plt.title("Simulation Results Comparison")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.grid()
    plt.tight_layout()

    # --- Histogramme des temps ---
    benchmarks = {
        'bench_01': {
            'bdsim':       np.median(times_bd) * 1e3,
            'PathSim':     np.median(times_ps) * 1e3,
            'pySimBlocks': np.median(times_pb) * 1e3,
        },
        # 'bench_02': { 'bdsim': ..., 'PathSim': ..., 'pySimBlocks': ... },
        # 'bench_03': { 'bdsim': ..., 'PathSim': ..., 'pySimBlocks': ... },
    }

    libs = ['bdsim', 'PathSim', 'pySimBlocks']
    colors = {'bdsim': '#7F77DD', 'PathSim': '#1D9E75', 'pySimBlocks': '#D85A30'}

    n_bench = len(benchmarks)
    width = 0.25
    group_gap = 1.0  # espace entre groupes

    fig, ax = plt.subplots(figsize=(4 + 2 * n_bench, 5))

    for g, (bench_name, values) in enumerate(benchmarks.items()):
        group_center = g * group_gap
        offsets = [-width, 0, width]
        for lib, offset in zip(libs, offsets):
            val = values[lib]
            bar = ax.bar(group_center + offset, val, width=width,
                         color=colors[lib], label=lib if g == 0 else None)
            ax.bar_label(bar, fmt='%.1f', padding=3, fontsize=8)

    ax.set_xticks([g * group_gap for g in range(n_bench)])
    ax.set_xticklabels(list(benchmarks.keys()))
    ax.set_ylabel('Median time (ms)')
    ax.set_title('Time benchmark comparison')
    ax.set_yscale('log')
    ax.legend(loc='upper right')
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.spines[['top', 'right']].set_visible(False)

    plt.tight_layout()
    plt.show()
