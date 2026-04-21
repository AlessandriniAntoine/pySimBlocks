"""
bench_01_minimal_loop — Comparison
====================================
Runs the benchmark across all simulators and reports:
  - Execution times (median, std)
  - Numerical errors between simulators (L2 norm)
  - Signal plots
  - Execution time bar chart (log scale)

Simulink results are loaded from a pre-generated CSV file (matlab/simulink_results.csv).
bdsim is commented out as it is too slow for repeated runs.
"""

import logging

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from pathsim_case import test_pathsim_case
from pysimblocks_case import test_pysimblocks_case
# from bdsim_case import test_bdsim_case


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    N_RUNS = 100

    logger.info(f"Running benchmark ({N_RUNS} runs each)...")

    results_ps, results_pb = [], []
    # results_bd = []
    for i in range(N_RUNS):
        print(f"  Run {i+1}/{N_RUNS}...", end="\r")
        results_ps.append(test_pathsim_case())
        results_pb.append(test_pysimblocks_case())
        # results_bd.append(test_bdsim_case())

    print()

    # ── Timing arrays ─────────────────────────────────────────────────────────
    times_ps = np.array([r[3] for r in results_ps]) * 1e3   # s → ms
    times_pb = np.array([r[3] for r in results_pb]) * 1e3
    # times_bd = np.array([r[3] for r in results_bd]) * 1e3

    # ── Simulink results (pre-generated) ─────────────────────────────────────
    sl        = np.loadtxt(Path(__file__).parent / "matlab" / "simulink_results.csv", delimiter=",", skiprows=1)
    t_sl      = sl[:, 0]
    noise_sl  = sl[:, 1]
    output_sl = sl[:, 2]
    t_mean_sl = 143.3   # ms  — measured separately over 100 runs
    t_std_sl  = 6.7     # ms

    # ── Last-run signals ──────────────────────────────────────────────────────
    t_ps, noise_ps, output_ps, _ = results_ps[-1]
    t_pb, noise_pb, output_pb, _ = results_pb[-1]
    # t_bd, noise_bd, output_bd, _ = results_bd[-1]

    n = min(len(t_ps), len(t_pb), len(t_sl))
    t_ps, noise_ps, output_ps = t_ps[:n], noise_ps[:n], output_ps[:n]
    t_pb, noise_pb, output_pb = t_pb[:n], noise_pb[:n], output_pb[:n]
    t_sl, noise_sl, output_sl = t_sl[:n], noise_sl[:n], output_sl[:n]
    # t_bd, noise_bd, output_bd = t_bd[:n], noise_bd[:n], output_bd[:n]

    # ── Numerical errors (L2 norm) ────────────────────────────────────────────
    def rel(err, ref):
        return err / np.linalg.norm(ref) * 100 if np.linalg.norm(ref) > 0 else 0.0

    t_err_ps     = np.linalg.norm(t_ps    - t_pb)
    noise_err_ps = np.linalg.norm(noise_ps - noise_pb)
    out_err_ps   = np.linalg.norm(output_ps - output_pb)

    t_err_sl     = np.linalg.norm(t_sl    - t_pb)
    noise_err_sl = np.linalg.norm(noise_sl - noise_pb)
    out_err_sl   = np.linalg.norm(output_sl - output_pb)

    # ── Save reference results ────────────────────────────────────────────────
    np.savez(Path(__file__).parent / "reference_results.npz",
        t           = t_pb,
        noise       = noise_pb,
        output_psb  = output_pb,
        output_ps   = output_ps,
        # output_bd   = output_bd,
        output_sl   = output_sl,
        times_ps_ms = times_ps,
        times_pb_ms = times_pb,
        # times_bd_ms = times_bd,
        t_sl        = t_sl,
    )

    # ── Console report ────────────────────────────────────────────────────────
    logger.info("")
    logger.info("=== Timing ===")
    logger.info(f"  PathSim:     median={np.median(times_ps):.1f} ms,  std={np.std(times_ps):.1f} ms")
    logger.info(f"  pySimBlocks: median={np.median(times_pb):.1f} ms,  std={np.std(times_pb):.1f} ms")
    logger.info(f"  Simulink:    median={t_mean_sl:.1f} ms,  std={t_std_sl:.1f} ms")
    # logger.info(f"  bdsim:       median={np.median(times_bd):.1f} ms,  std={np.std(times_bd):.1f} ms")
    logger.info(f"  Speedup pySimBlocks vs PathSim:  {np.median(times_ps) / np.median(times_pb):.2f}x")
    logger.info(f"  Speedup pySimBlocks vs Simulink: {t_mean_sl / np.median(times_pb):.2f}x")

    logger.info("")
    logger.info("=== Numerical errors — L2 norm (last run) ===")
    logger.info(f"{'Comparison':<30} {'Time':>16} {'Noise':>16} {'Output':>16}")
    logger.info("-" * 82)
    logger.info(
        f"{'PathSim vs pySimBlocks':<30} "
        f"{t_err_ps:.2e} ({rel(t_err_ps, t_pb):.2f}%)  "
        f"{noise_err_ps:.2e} ({rel(noise_err_ps, noise_pb):.2f}%)  "
        f"{out_err_ps:.2e} ({rel(out_err_ps, output_pb):.2f}%)"
    )
    logger.info(
        f"{'Simulink vs pySimBlocks':<30} "
        f"{t_err_sl:.2e} ({rel(t_err_sl, t_pb):.2f}%)  "
        f"{noise_err_sl:.2e} ({rel(noise_err_sl, noise_pb):.2f}%)  "
        f"{out_err_sl:.2e} ({rel(out_err_sl, output_pb):.2f}%)"
    )

    # ── Signal plot ───────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(t_ps, noise_ps,  "--r",  label="Noise (PathSim)",     alpha=0.7)
    ax.plot(t_ps, output_ps, "--b",  label="Output (PathSim)",    alpha=0.7)
    ax.plot(t_pb, noise_pb,  ":r",   label="Noise (pySimBlocks)", alpha=0.7)
    ax.plot(t_pb, output_pb, ":b",   label="Output (pySimBlocks)",alpha=0.7)
    ax.plot(t_sl, noise_sl,  "-.m",  label="Noise (Simulink)",    alpha=0.7)
    ax.plot(t_sl, output_sl, "-.c",  label="Output (Simulink)",   alpha=0.7)
    # ax.plot(t_bd, noise_bd,  "-.r", label="Noise (bdsim)",       alpha=0.7)
    # ax.plot(t_bd, output_bd, "-.b", label="Output (bdsim)",      alpha=0.7)
    ax.set_title("bench_01 — Signal comparison")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    # ── Timing bar chart (log scale) ──────────────────────────────────────────
    timings = {
        "PathSim":     np.median(times_ps),
        "pySimBlocks": np.median(times_pb),
        "Simulink":    t_mean_sl,
        # "bdsim":       np.median(times_bd),
    }
    errors = {
        "PathSim":     np.std(times_ps),
        "pySimBlocks": np.std(times_pb),
        "Simulink":    t_std_sl,
    }
    colors = {
        "PathSim":     "#1D9E75",
        "pySimBlocks": "#D85A30",
        "Simulink":    "#E1B000",
        # "bdsim":       "#5B7FD4",
    }

    fig2, ax2 = plt.subplots(figsize=(6, 5))
    for i, (lib, val) in enumerate(timings.items()):
        bar = ax2.bar(i, val, color=colors[lib], label=lib,
                      yerr=errors[lib], capsize=4, width=0.5)
        ax2.bar_label(bar, fmt="%.1f", padding=4, fontsize=9)

    ax2.set_xticks(range(len(timings)))
    ax2.set_xticklabels(list(timings.keys()))
    ax2.set_ylabel("Median execution time (ms)")
    ax2.set_title("bench_01 — Execution time comparison")
    ax2.set_yscale("log")
    ax2.legend(loc="upper right")
    ax2.grid(axis="y", linestyle="--", alpha=0.4)
    ax2.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()

    plt.show()
