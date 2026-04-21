"""
bench_03_scaling — PathSim
===========================
Measures simulation time as a function of the number of blocks.

Same topology as the pySimBlocks version:

    noise → G0 → S0(++) → Dyn0(Integ) → Gcouple0 → S1(+++) → Dyn1(Delay) → Gcouple1 → ...
                    ↑           |                       ↑  ↑          |
                 GainFb0 ←──────┘                Gcouple0 Gain1    GainFb1←──┘

Per cell i:
  - Gain_i      : feedforward Amplifier from noise
  - Sum_i       : Adder (++ for cell 0, +++ for cells i>0)
  - Dyn_i       : Integrator if i even, Delay if i odd
  - GainFb_i    : local feedback Amplifier
  - Gcouple_i   : inter-cell coupling Amplifier (except last cell)

Total blocks ≈ 5*N  |  RK4 solver, fixed step (adaptive=False)
"""

from __future__ import annotations

from pathlib import Path
import time
import statistics

import numpy as np
import matplotlib.pyplot as plt

from pathsim import Simulation, Connection
from pathsim.blocks import Adder, Amplifier, Integrator, Delay, Source
from pathsim.solvers import EUF


# ─────────────────────────────────────────────────────────────────────────────
# Parameters
# ─────────────────────────────────────────────────────────────────────────────

DT      = 0.001
N_STEPS = 100_000
T       = N_STEPS * DT

N_RUNS       = 3
N_CELLS_LIST = [5, 10, 20, 50, 100]


# ─────────────────────────────────────────────────────────────────────────────
# Model builder
# ─────────────────────────────────────────────────────────────────────────────

def build_pathsim_scaling(n_cells: int):
    """Build PathSim blocks and connections for n_cells cascaded cells.

    Args:
        n_cells: Number of cells (>= 2).

    Returns:
        Tuple (blocks, connections).
    """
    if n_cells < 2:
        raise ValueError("n_cells must be >= 2")

    # ── Source ────────────────────────────────────────────────────────────────
    rng = np.random.default_rng(0)
    noise_seq = rng.standard_normal(N_STEPS + 2)

    def make_source(seq, dt):
        def f(t):
            k = int(round(t / dt))
            return float(seq[min(k, len(seq) - 1)])
        return Source(f)

    src = make_source(noise_seq, DT)

    # ── Per-cell blocks ───────────────────────────────────────────────────────
    gains     = []   # feedforward
    sums      = []
    dyns      = []   # Integrator or Delay
    gainfbs   = []   # local feedback
    gcouples  = []   # inter-cell coupling

    for i in range(n_cells):
        gain_val    = 0.5 / (i + 1)
        fb_gain     = 0.2 / (i + 1)
        couple_gain = 0.8 / (i + 1)

        gains.append(Amplifier(gain=gain_val))

        # Sum0: 2 inputs; Sum_i>0: 3 inputs — PathSim Adder infers nin from operations string
        ops = "++" if i == 0 else "+++"
        sums.append(Adder(operations=ops))

        if i % 2 == 0:
            dyns.append(Integrator())
        else:
            dyns.append(Delay(tau=DT))

        gainfbs.append(Amplifier(gain=fb_gain))

        if i < n_cells - 1:
            gcouples.append(Amplifier(gain=couple_gain))

    # ── Assemble block list ───────────────────────────────────────────────────
    blocks = [src]
    for i in range(n_cells):
        blocks += [gains[i], sums[i], dyns[i], gainfbs[i]]
        if i < n_cells - 1:
            blocks.append(gcouples[i])

    # ── Connections ───────────────────────────────────────────────────────────
    connections = []

    # noise → all Gain_i (fan-out)
    for i in range(n_cells):
        connections.append(Connection(src[0], gains[i][0]))

    for i in range(n_cells):
        # Sum_i.in1
        if i == 0:
            connections.append(Connection(gains[0][0], sums[0][0]))
        else:
            connections.append(Connection(gcouples[i - 1][0], sums[i][0]))

        # Sum_i.in2: local feedback
        connections.append(Connection(gainfbs[i][0], sums[i][1]))

        # Sum_i → Dyn_i
        connections.append(Connection(sums[i][0], dyns[i][0]))

        # Dyn_i → GainFb_i (local feedback loop)
        connections.append(Connection(dyns[i][0], gainfbs[i][0]))

        # Dyn_i → Gcouple_i (coupling to next cell)
        if i < n_cells - 1:
            connections.append(Connection(dyns[i][0], gcouples[i][0]))

    # Gain_i (i>0) → Sum_i.in3 (feedforward for cells i>0)
    for i in range(1, n_cells):
        connections.append(Connection(gains[i][0], sums[i][2]))

    return blocks, connections


# ─────────────────────────────────────────────────────────────────────────────
# Benchmark
# ─────────────────────────────────────────────────────────────────────────────

def run_benchmark(n_cells: int, n_runs: int) -> dict:
    """Run n_runs simulations for n_cells cells and return timing stats."""
    n_total_blocks = 5 * n_cells
    times = []

    for _ in range(n_runs):
        blocks, connections = build_pathsim_scaling(n_cells)

        sim = Simulation(
            blocks,
            connections,
            Solver=EUF,
            dt=DT,
            dt_min=DT,
            dt_max=DT,
            tolerance_lte_rel=1e-4,
            tolerance_lte_abs=1e-8,
            tolerance_fpi=1e-10,
            log=False,
        )

        t0 = time.perf_counter()
        sim.run(duration=T, reset=True, adaptive=False)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000)  # ms

    return {
        "n_cells": n_cells,
        "n_blocks": n_total_blocks,
        "median_ms": statistics.median(times),
        "std_ms": statistics.stdev(times) if len(times) > 1 else 0.0,
        "min_ms": min(times),
        "max_ms": max(times),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Bench Scaling (PathSim) — {N_STEPS} steps, dt={DT}, {N_RUNS} runs each\n")
    print(f"{'n_cells':>8} {'n_blocks':>10} {'median (ms)':>14} {'std (ms)':>10}")
    print("-" * 46)

    results = []
    for n in N_CELLS_LIST:
        r = run_benchmark(n, N_RUNS)
        results.append(r)
        print(f"{r['n_cells']:>8} {r['n_blocks']:>10} {r['median_ms']:>14.1f} {r['std_ms']:>10.1f}")

    np.savez(
        Path(__file__).parent / "bench_scaling_pathsim_results.npz",
        results=results,
        N_STEPS=N_STEPS,
        N_RUNS=N_RUNS,
        DT=DT,
        N_CELLS_LIST=N_CELLS_LIST,
    )

    # ── Plot ──────────────────────────────────────────────────────────────────
    n_blocks = [r["n_blocks"] for r in results]
    medians  = [r["median_ms"] for r in results]
    stds     = [r["std_ms"] for r in results]

    coeffs   = np.polyfit(n_blocks, medians, 1)
    fit_line = np.poly1d(coeffs)
    n_fit    = np.linspace(min(n_blocks), max(n_blocks), 200)

    us_per_step_per_block = [
        (m / N_STEPS * 1000) / nb
        for m, nb in zip(medians, n_blocks)
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(
        f"PathSim — Simulation time scaling\n"
        f"({N_STEPS} steps, dt={DT}, {N_RUNS} runs/point)",
        fontsize=12,
    )

    ax = axes[0]
    ax.errorbar(n_blocks, medians, yerr=stds, fmt="o-", color="#1D9E75",
                capsize=4, label="Measured median")
    ax.plot(n_fit, fit_line(n_fit), "--", color="tomato", alpha=0.7,
            label=f"Linear fit ({coeffs[0]:.2f} ms/block)")
    ax.set_xlabel("Number of blocks")
    ax.set_ylabel("Simulation time (ms)")
    ax.set_title("Absolute time")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax2 = axes[1]
    ax2.plot(n_blocks, us_per_step_per_block, "s-", color="#1D9E75")
    ax2.set_xlabel("Number of blocks")
    ax2.set_ylabel("Cost per step per block (µs)")
    ax2.set_title("Unit cost per block per step")
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=np.mean(us_per_step_per_block), color="tomato",
                linestyle="--", alpha=0.7,
                label=f"Mean: {np.mean(us_per_step_per_block):.2f} µs")
    ax2.legend()

    plt.tight_layout()
    plt.show()
