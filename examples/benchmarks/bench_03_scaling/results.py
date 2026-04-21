from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":

    data = np.load(Path(__file__).parent / "bench_scaling_results.npz", allow_pickle=True)
    results = data["results"]
    N_STEPS = data["N_STEPS"].item()
    N_RUNS = data["N_RUNS"].item()
    DT = data["DT"].item()
    N_CELLS_LIST = data["N_CELLS_LIST"]


    print(f"Bench Scaling — {N_STEPS} steps, dt={DT}, {N_RUNS} runs each\n")
    print(f"{'n_cells':>8} {'n_blocks':>10} {'n_conn':>8} {'median (ms)':>14} {'std (ms)':>10}")
    print("-" * 54)

    for n, r in zip(N_CELLS_LIST, results):
        print(f"{r['n_cells']:>8} {r['n_blocks']:>10} {r['n_connections']:>8} "
              f"{r['median_ms']:>14.1f} {r['std_ms']:>10.1f}")

    # ── Plot ──────────────────────────────────────────────────────────────────
    n_blocks = [r["n_blocks"] for r in results]
    medians  = [r["median_ms"] for r in results]
    stds     = [r["std_ms"] for r in results]

    coeffs   = np.polyfit(n_blocks, medians, 1)
    fit_line = np.poly1d(coeffs)
    n_fit    = np.linspace(min(n_blocks), max(n_blocks), 200)

    # Cost per step per block in µs
    us_per_step_per_block = [
        (m / N_STEPS * 1000) / nb
        for m, nb in zip(medians, n_blocks)
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(
        f"pySimBlocks — Simulation time scaling\n"
        f"({N_STEPS} steps, dt={DT}, {N_RUNS} runs/point)",
        fontsize=12,
    )

    ax = axes[0]
    ax.errorbar(n_blocks, medians, yerr=stds, fmt="o-", color="steelblue",
                capsize=4, label="Measured median")
    ax.plot(n_fit, fit_line(n_fit), "--", color="tomato", alpha=0.7,
            label=f"Linear fit ({coeffs[0]:.2f} ms/block)")
    ax.set_xlabel("Number of blocks")
    ax.set_ylabel("Simulation time (ms)")
    ax.set_title("Absolute time")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax2 = axes[1]
    ax2.plot(n_blocks, us_per_step_per_block, "s-", color="seagreen")
    ax2.set_xlabel("Number of blocks")
    ax2.set_ylabel("Cost per step per block (µs)")
    ax2.set_title("Unit cost per block per step")
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=np.mean(us_per_step_per_block), color="tomato",
                linestyle="--", alpha=0.7, label=f"Mean: {np.mean(us_per_step_per_block):.2f} µs")
    ax2.legend()

    plt.tight_layout()
    plt.show()

