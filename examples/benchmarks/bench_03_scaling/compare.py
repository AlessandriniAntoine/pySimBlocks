"""
bench_03_scaling — Comparison
===============================
Loads pre-computed results from pySimBlocks and PathSim scaling benchmarks
and produces a side-by-side comparison:
  - Absolute time vs number of blocks (both simulators on same plot)
  - Unit cost per block per step (µs) vs number of blocks
  - Console report with slopes and mean unit costs
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


if __name__ == "__main__":

    # ── Load results ──────────────────────────────────────────────────────────
    data_pb = np.load(Path(__file__).parent / "bench_scaling_results.npz", allow_pickle=True)
    results_pb = data_pb["results"]
    N_STEPS    = data_pb["N_STEPS"].item()
    N_RUNS     = data_pb["N_RUNS"].item()
    DT         = data_pb["DT"].item()

    data_ps = np.load(Path(__file__).parent / "bench_scaling_pathsim_results.npz", allow_pickle=True)
    results_ps = data_ps["results"]

    # ── Extract arrays ────────────────────────────────────────────────────────
    n_blocks_pb = [r["n_blocks"]  for r in results_pb]
    medians_pb  = [r["median_ms"] for r in results_pb]
    stds_pb     = [r["std_ms"]    for r in results_pb]

    n_blocks_ps = [r["n_blocks"]  for r in results_ps]
    medians_ps  = [r["median_ms"] for r in results_ps]
    stds_ps     = [r["std_ms"]    for r in results_ps]

    # ── Unit costs (µs/block/step) ────────────────────────────────────────────
    us_pb = [(m / N_STEPS * 1000) / nb for m, nb in zip(medians_pb, n_blocks_pb)]
    us_ps = [(m / N_STEPS * 1000) / nb for m, nb in zip(medians_ps, n_blocks_ps)]

    # ── Linear fits ───────────────────────────────────────────────────────────
    coeffs_pb = np.polyfit(n_blocks_pb, medians_pb, 1)
    coeffs_ps = np.polyfit(n_blocks_ps, medians_ps, 1)

    n_fit = np.linspace(min(min(n_blocks_pb), min(n_blocks_ps)),
                        max(max(n_blocks_pb), max(n_blocks_ps)), 200)

    # ── Console report ────────────────────────────────────────────────────────
    print(f"Bench Scaling Comparison — {N_STEPS} steps, dt={DT}, {N_RUNS} runs each\n")
    print(f"{'n_blocks':>10} {'psb median (ms)':>18} {'psb std':>10} {'ps median (ms)':>16} {'ps std':>10}")
    print("-" * 68)
    for nb_pb, m_pb, s_pb, nb_ps, m_ps, s_ps in zip(
        n_blocks_pb, medians_pb, stds_pb,
        n_blocks_ps, medians_ps, stds_ps,
    ):
        print(f"{nb_pb:>10} {m_pb:>18.1f} {s_pb:>10.1f} {m_ps:>16.1f} {s_ps:>10.1f}")

    print()
    print(f"Linear fit slope — pySimBlocks : {coeffs_pb[0]:.2f} ms/block")
    print(f"Linear fit slope — PathSim     : {coeffs_ps[0]:.2f} ms/block")
    print(f"Mean unit cost   — pySimBlocks : {np.mean(us_pb):.2f} µs/block/step")
    print(f"Mean unit cost   — PathSim     : {np.mean(us_ps):.2f} µs/block/step")
    print(f"Slope ratio PathSim / pySimBlocks : {coeffs_ps[0] / coeffs_pb[0]:.2f}x")

    # ── Plot ──────────────────────────────────────────────────────────────────
    colors = {"pb": "#D85A30", "ps": "#1D9E75"}

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(
        f"bench_03 — Simulation time scaling: pySimBlocks vs PathSim\n"
        f"({N_STEPS} steps, dt={DT}, {N_RUNS} runs/point)",
        fontsize=12,
    )

    # Left: absolute time
    ax = axes[0]
    ax.errorbar(n_blocks_pb, medians_pb, yerr=stds_pb, fmt="o-",
                color=colors["pb"], capsize=4, label="pySimBlocks")
    ax.errorbar(n_blocks_ps, medians_ps, yerr=stds_ps, fmt="s-",
                color=colors["ps"], capsize=4, label="PathSim (RK4, fixed step)")
    ax.plot(n_fit, np.poly1d(coeffs_pb)(n_fit), "--", color=colors["pb"], alpha=0.5,
            label=f"psb fit ({coeffs_pb[0]:.1f} ms/block)")
    ax.plot(n_fit, np.poly1d(coeffs_ps)(n_fit), "--", color=colors["ps"], alpha=0.5,
            label=f"ps fit  ({coeffs_ps[0]:.1f} ms/block)")
    ax.set_xlabel("Number of blocks")
    ax.set_ylabel("Simulation time (ms)")
    ax.set_title("Absolute time")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Right: unit cost per block per step
    ax2 = axes[1]
    ax2.plot(n_blocks_pb, us_pb, "o-", color=colors["pb"], label="pySimBlocks")
    ax2.plot(n_blocks_ps, us_ps, "s-", color=colors["ps"], label="PathSim")
    ax2.axhline(y=np.mean(us_pb), color=colors["pb"], linestyle="--", alpha=0.6,
                label=f"psb mean: {np.mean(us_pb):.2f} µs")
    ax2.axhline(y=np.mean(us_ps), color=colors["ps"], linestyle="--", alpha=0.6,
                label=f"ps  mean: {np.mean(us_ps):.2f} µs")
    ax2.set_xlabel("Number of blocks")
    ax2.set_ylabel("Cost per step per block (µs)")
    ax2.set_title("Unit cost per block per step")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()
