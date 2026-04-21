"""
bench_03_scaling — pySimBlocks
================================
Measures simulation time as a function of the number of blocks.

Topology per cell (N=3 example):

    noise → G0 → S0(++) → Dyn0(Integ) → Gcouple0 → S1(+++) → Dyn1(Delay) → Gcouple1 → S2(+++) → Dyn2(Integ)
                    ↑           |                       ↑  ↑          |                     ↑  ↑
                 GainFb0 ←──────┘                Gcouple0 Gain1    GainFb1←──┘          Gcouple1 Gain2
                                                                                          GainFb2←──┘

Per cell i:
  - Gain_i      : feedforward from noise
  - Sum_i       : sum (2 inputs for cell 0, 3 inputs for cells i>0)
  - Dyn_i       : discrete_integrator if i even, delay if i odd
  - GainFb_i    : local feedback (Dyn_i.out → GainFb_i → Sum_i.in2)
  - Gcouple_i   : inter-cell coupling (Dyn_i.out → Gcouple_i → Sum_{i+1}.in1)  [except last]

Total blocks = 5*N (source included)
Total connections ≈ 5*N
"""

from __future__ import annotations

import time
import statistics
import tempfile
from pathlib import Path

import numpy as np
import yaml
import matplotlib.pyplot as plt

from pySimBlocks.project import load_simulator_from_project


# ─────────────────────────────────────────────────────────────────────────────
# Parameters
# ─────────────────────────────────────────────────────────────────────────────

DT = 0.001
N_STEPS = 100_000
T = N_STEPS * DT

N_RUNS = 3
N_CELLS_LIST = [5, 10, 20, 50, 100]


# ─────────────────────────────────────────────────────────────────────────────
# YAML generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_project_dict(n_cells: int, dt: float = DT, T: float = T) -> dict:
    """Generate a project.yaml dict for n_cells cascaded cells.

    Topology:
        Sum0 receives: Gain0.out (in1) + GainFb0.out (in2)
        Sum_i (i>0) receives: Gcouple_{i-1}.out (in1) + GainFb_i.out (in2) + Gain_i.out (in3)
        Dyn_i.out → GainFb_i → Sum_i.in2  (local feedback)
        Dyn_i.out → Gcouple_i → Sum_{i+1}.in1  (inter-cell coupling)
        noise → all Gain_i  (fan-out)

    Args:
        n_cells: Number of cells (>= 2).
        dt: Simulation time step.
        T: Total simulation duration.

    Returns:
        Dict ready to serialize as YAML.
    """
    if n_cells < 2:
        raise ValueError("n_cells must be >= 2")

    blocks = []
    connections = []
    conn_idx = 1

    def add(src: str, dst: str) -> None:
        nonlocal conn_idx
        connections.append({"name": f"c{conn_idx}", "ports": [src, dst]})
        conn_idx += 1

    # ── Source ────────────────────────────────────────────────────────────────
    blocks.append({
        "name": "WhiteNoise",
        "category": "sources",
        "type": "white_noise",
        "parameters": {"std": 1.0},
    })

    # ── Cells ─────────────────────────────────────────────────────────────────
    for i in range(n_cells):
        gain_val    = round(0.5 / (i + 1), 6)
        dyn_type    = "discrete_integrator" if i % 2 == 0 else "delay"
        couple_gain = round(0.8 / (i + 1), 6)
        fb_gain     = round(0.2 / (i + 1), 6)

        blocks.append({
            "name": f"Gain{i}",
            "category": "operators",
            "type": "gain",
            "parameters": {"gain": gain_val, "multiplication": "Element wise (K * u)"},
        })
        # Sum0: 2 inputs (++)  |  Sum_i>0: 3 inputs (+++) — corrected below
        blocks.append({
            "name": f"Sum{i}",
            "category": "operators",
            "type": "sum",
            "parameters": {"signs": "++"},
        })
        blocks.append({
            "name": f"Dyn{i}",
            "category": "operators",
            "type": dyn_type,
            "parameters": {},
        })
        blocks.append({
            "name": f"GainFb{i}",
            "category": "operators",
            "type": "gain",
            "parameters": {"gain": fb_gain, "multiplication": "Element wise (K * u)"},
        })
        if i < n_cells - 1:
            blocks.append({
                "name": f"Gcouple{i}",
                "category": "operators",
                "type": "gain",
                "parameters": {"gain": couple_gain, "multiplication": "Element wise (K * u)"},
            })

    # Cells i>0 have 3 inputs: Gcouple_{i-1} + GainFb_i + Gain_i
    for b in blocks:
        if b["name"].startswith("Sum") and b["name"] != "Sum0":
            b["parameters"]["signs"] = "+++"

    # ── Connections ───────────────────────────────────────────────────────────

    # noise → all Gain_i (fan-out)
    for i in range(n_cells):
        add("WhiteNoise.out", f"Gain{i}.in")

    for i in range(n_cells):
        # Sum_i.in1: Gain0.out for cell 0, Gcouple_{i-1}.out for cells i>0
        if i == 0:
            add("Gain0.out", "Sum0.in1")
        else:
            add(f"Gcouple{i-1}.out", f"Sum{i}.in1")

        # Sum_i.in2: local feedback
        add(f"GainFb{i}.out", f"Sum{i}.in2")

        # Sum_i → Dyn_i
        add(f"Sum{i}.out", f"Dyn{i}.in")

        # Dyn_i → GainFb_i (local feedback loop)
        add(f"Dyn{i}.out", f"GainFb{i}.in")

        # Dyn_i → Gcouple_i (coupling to next cell)
        if i < n_cells - 1:
            add(f"Dyn{i}.out", f"Gcouple{i}.in")

    # Gain_i (i>0) → Sum_i.in3 (feedforward for cells i>0)
    for i in range(1, n_cells):
        add(f"Gain{i}.out", f"Sum{i}.in3")

    n_total_blocks = 5 * n_cells  # source + 4 blocks/cell + (n-1) coupling gains ≈ 5N
    n_connections  = conn_idx - 1

    return {
        "schema_version": 1,
        "project": {"name": f"bench_scaling_{n_cells}_cells"},
        "simulation": {
            "dt": dt,
            "T": T,
            "solver": "fixed",
            "logging": [f"Dyn{n_cells - 1}.outputs.out"],
            "plots": [],
        },
        "diagram": {
            "blocks": blocks,
            "connections": connections,
        },
        "_meta": {
            "n_cells": n_cells,
            "n_blocks": n_total_blocks,
            "n_connections": n_connections,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Benchmark
# ─────────────────────────────────────────────────────────────────────────────

def run_benchmark(n_cells: int, n_runs: int) -> dict:
    """Run n_runs simulations for n_cells cells and return timing stats."""
    meta = generate_project_dict(n_cells)["_meta"]
    n_total_blocks = meta["n_blocks"]
    times = []

    project_dict = generate_project_dict(n_cells)

    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_path = Path(tmpdir) / "project.yaml"
        with open(yaml_path, "w") as f:
            d = {k: v for k, v in project_dict.items() if k != "_meta"}
            yaml.dump(d, f, default_flow_style=False, sort_keys=False)

        for _ in range(n_runs):
            sim, _ = load_simulator_from_project(yaml_path)
            t0 = time.perf_counter()
            sim.run()
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000)  # ms

    return {
        "n_cells": n_cells,
        "n_blocks": n_total_blocks,
        "n_connections": meta["n_connections"],
        "median_ms": statistics.median(times),
        "std_ms": statistics.stdev(times) if len(times) > 1 else 0.0,
        "min_ms": min(times),
        "max_ms": max(times),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Bench Scaling — {N_STEPS} steps, dt={DT}, {N_RUNS} runs each\n")
    print(f"{'n_cells':>8} {'n_blocks':>10} {'n_conn':>8} {'median (ms)':>14} {'std (ms)':>10}")
    print("-" * 54)

    results = []
    for n in N_CELLS_LIST:
        r = run_benchmark(n, N_RUNS)
        results.append(r)
        print(f"{r['n_cells']:>8} {r['n_blocks']:>10} {r['n_connections']:>8} "
              f"{r['median_ms']:>14.1f} {r['std_ms']:>10.1f}")
    
    np.savez(Path(__file__).parent / "bench_scaling_results.npz", 
             results=results,
             N_STEPS=N_STEPS,
             N_RUNS=N_RUNS,
             DT=DT,
             N_CELLS_LIST=N_CELLS_LIST
             )

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
