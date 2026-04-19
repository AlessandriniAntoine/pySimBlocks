"""
Comparaison des résultats de simulation entre différentes librairies (bdsim, PathSim, pySimBlocks, Simulink).
- Charge les résultats de chaque librairie (temps, signal de bruit, signal de sortie).
- Calcule les erreurs numériques entre les librairies (norme de la différence).
- Affiche les résultats dans la console (temps, erreurs).
- Trace les signaux de bruit et de sortie pour chaque librairie sur un même graphique.
- Affiche un histogramme comparant les temps de simulation des différentes librairies.

Rq: (Bdsim est commenté car trop lent)
"""
import logging

import numpy as np
import matplotlib.pyplot as plt

from bdsim_case import test_bdsim_case
from pathsim_case import test_pathsim_case
from pysimblocks_case import test_pysimblocks_case


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    N_RUNS = 100

    logger.info(f"Running benchmark ({N_RUNS} runs each)...")

    results_bd, results_ps, results_pb = [], [], []
    for i in range(N_RUNS):
        print(f"Run {i+1}/{N_RUNS}...", end="\r")
        # results_bd.append(test_bdsim_case())
        results_ps.append(test_pathsim_case())
        results_pb.append(test_pysimblocks_case())

    # times_bd = np.array([r[3] for r in results_bd])
    times_ps = np.array([r[3] for r in results_ps])
    times_pb = np.array([r[3] for r in results_pb])

    sl = np.loadtxt("matlab/simulink_results.csv", delimiter=",", skiprows=1)
    t_sl      = sl[:, 0]
    noise_sl  = sl[:, 1]
    output_sl = sl[:, 2]
    t_mean_sl = 143.3 # ms
    t_std_sl = 6.7 # ms

    # t_bd, noise_bd, output_bd, _ = results_bd[-1]
    t_ps, noise_ps, output_ps, _ = results_ps[-1]
    t_pb, noise_pb, output_pb, _ = results_pb[-1]

    n = min(len(t_ps), len(t_pb), len(t_sl))
    # t_bd, noise_bd, output_bd = t_bd[:n], noise_bd[:n], output_bd[:n]
    t_ps, noise_ps, output_ps = t_ps[:n], noise_ps[:n], output_ps[:n]
    t_pb, noise_pb, output_pb = t_pb[:n], noise_pb[:n], output_pb[:n]
    t_sl, noise_sl, output_sl = t_sl[:n], noise_sl[:n], output_sl[:n]
    
    # t_error_bd_pb = np.linalg.norm(t_bd - t_pb)
    # noise_error_bd_pb = np.linalg.norm(noise_bd - noise_pb)
    # output_error_bd_pb = np.linalg.norm(output_bd - output_pb)
    t_error_ps_pb = np.linalg.norm(t_ps - t_pb)
    noise_error_ps_pb = np.linalg.norm(noise_ps - noise_pb)
    output_error_ps_pb = np.linalg.norm(output_ps - output_pb)
    t_error_sl_pb = np.linalg.norm(t_sl - t_pb)
    noise_error_sl_pb = np.linalg.norm(noise_sl - noise_pb)
    output_error_sl_pb = np.linalg.norm(output_sl - output_pb)

    # --- Sauvegarder les résultats de référence ---
    np.savez("reference_results.npz",
        t            = t_pb,
        noise        = noise_pb,
        output_psb   = output_pb,
        output_ps    = output_ps,
        # output_bd    = output_bd,
        output_sl    = output_sl,
        # times_bd_ms  = times_bd * 1e3,
        times_ps_ms  = times_ps * 1e3,
        times_pb_ms  = times_pb * 1e3,
        t_sl         = t_sl,
    )

    logger.info("")
    logger.info("=== Timing ===")
    # logger.info(f"  bdsim:       median={np.median(times_bd)*1e3:.1f} ms,  std={np.std(times_bd)*1e3:.1f} ms")
    logger.info(f"  PathSim:     median={np.median(times_ps)*1e3:.1f} ms,  std={np.std(times_ps)*1e3:.1f} ms")
    logger.info(f"  pySimBlocks: median={np.median(times_pb)*1e3:.1f} ms,  std={np.std(times_pb)*1e3:.1f} ms")
    logger.info(f"  Simulink:    median={t_mean_sl:.1f} ms,  std={t_std_sl:.1f} ms")
    logger.info(f"  Speedup pySimBlocks vs PathSim: {np.median(times_ps) / np.median(times_pb):.2f}x")
    # logger.info(f"  Speedup pySimBlocks vs bdsim:   {np.median(times_bd) / np.median(times_pb):.2f}x")
    logger.info(f"  Speedup pySimBlocks vs Simulink: {t_mean_sl*1e-3 / np.median(times_pb):.2f}x")

    logger.info("")
    logger.info("=== Numerical errors (last run) ===")
    logger.info("Librairies | Time error (a/b%) | Noise error (a/b%) | Output error (a/b%)")
    # logger.info(f"bdsim vs pySimBlocks | {t_error_bd_pb:.2e} ({t_error_bd_pb / np.linalg.norm(t_pb) * 100:.2f}%) | {noise_error_bd_pb:.2e} ({noise_error_bd_pb / np.linalg.norm(noise_pb) * 100:.2f}%) | {output_error_bd_pb:.2e} ({output_error_bd_pb / np.linalg.norm(output_pb) * 100:.2f}%)")
    logger.info(f"PathSim vs pySimBlocks | {t_error_ps_pb:.2e} ({t_error_ps_pb / np.linalg.norm(t_pb) * 100:.2f}%) | {noise_error_ps_pb:.2e} ({noise_error_ps_pb / np.linalg.norm(noise_pb) * 100:.2f}%) | {output_error_ps_pb:.2e} ({output_error_ps_pb / np.linalg.norm(output_pb) * 100:.2f}%)")
    logger.info(f"Simulink vs pySimBlocks | {t_error_sl_pb:.2e} ({t_error_sl_pb / np.linalg.norm(t_pb) * 100:.2f}%) | {noise_error_sl_pb:.2e} ({noise_error_sl_pb / np.linalg.norm(noise_pb) * 100:.2f}%) | {output_error_sl_pb:.2e} ({output_error_sl_pb / np.linalg.norm(output_pb) * 100:.2f}%)")

    plt.figure(figsize=(10, 6))
    # plt.plot(t_bd, noise_bd,  "-.r", label="Noise (bdsim)",     alpha=0.7)
    # plt.plot(t_bd, output_bd, "-.b", label="Output (bdsim)",    alpha=0.7)
    plt.plot(t_ps, noise_ps,  "--r", label="Noise (PathSim)",    alpha=0.7)
    plt.plot(t_ps, output_ps, "--b", label="Output (PathSim)",   alpha=0.7)
    plt.plot(t_pb, noise_pb,  ":r",  label="Noise (pySimBlocks)", alpha=0.7)
    plt.plot(t_pb, output_pb, ":b",  label="Output (pySimBlocks)", alpha=0.7)
    plt.plot(t_sl, noise_sl,  "-.m", label="Noise (Simulink)",   alpha=0.7)
    plt.plot(t_sl, output_sl, "-.c", label="Output (Simulink)",  alpha=0.7)
    plt.title("Simulation Results Comparison")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.grid()
    plt.tight_layout()

    # --- Histogramme des temps ---
    benchmarks = {
        'bench_01': {
            # 'bdsim':       np.median(times_bd) * 1e3,
            'PathSim':     np.median(times_ps) * 1e3,
            'pySimBlocks': np.median(times_pb) * 1e3,
            'Simulink':    t_mean_sl,
        },
    }

    libs = ['PathSim', 'pySimBlocks', 'Simulink']
    colors = {'PathSim': '#1D9E75', 'pySimBlocks': '#D85A30', 'Simulink': '#E1B000'}

    n_bench = len(benchmarks)
    width = 0.2
    group_gap = 1.0  # espace entre groupes

    fig, ax = plt.subplots(figsize=(4 + 2 * n_bench, 5))

    for g, (bench_name, values) in enumerate(benchmarks.items()):
        group_center = g * group_gap
        # offsets = [-1.5*width, -0.5*width, 0.5*width, 1.5*width]
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
