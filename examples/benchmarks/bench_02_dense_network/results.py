from pathlib import Path
import logging
import numpy as np
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

data = np.load(Path(__file__).parent / "reference_results.npz")
t = data["t"]
noise = data["noise"]
output_pb = data["output_psb"]
output_ps = data["output_ps"]
output_sl = data["output_sl"]
times_ps = data["times_ps_ms"]
times_pb = data["times_pb_ms"]
t_sl = data["t_sl"]
t_mean_sl = 253.5 # ms
t_std_sl = 12.5 # ms

logger.info("")
logger.info("=== Timing ===")
logger.info(f"  PathSim:     median={np.median(times_ps):.1f} ms,  std={np.std(times_ps):.1f} ms")
logger.info(f"  pySimBlocks: median={np.median(times_pb):.1f} ms,  std={np.std(times_pb):.1f} ms")
logger.info(f"  Simulink:    median={t_mean_sl:.1f} ms,  std={t_std_sl:.1f} ms")
logger.info(f"  Speedup pySimBlocks vs PathSim:  {np.median(times_ps) / np.median(times_pb):.2f}x")
logger.info(f"  Speedup pySimBlocks vs Simulink: {t_mean_sl / np.median(times_pb):.2f}x")

# ── Timing bar chart (log scale) ──────────────────────────────────────────
timings = {
    "PathSim":     np.median(times_ps),
    "pySimBlocks": np.median(times_pb),
    "Simulink":    t_mean_sl,
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
}

fig2, ax2 = plt.subplots(figsize=(6, 5))
for i, (lib, val) in enumerate(timings.items()):
    bar = ax2.bar(i, val, color=colors[lib], label=lib,
                  yerr=errors[lib], capsize=4, width=0.5)
    ax2.bar_label(bar, fmt="%.1f", padding=4, fontsize=9)

ax2.set_xticks(range(len(timings)))
ax2.set_xticklabels(list(timings.keys()))
ax2.set_ylabel("Median execution time (ms)")
ax2.set_title("bench_02 — Execution time comparison")
ax2.set_yscale("log")
ax2.legend(loc="upper right")
ax2.grid(axis="y", linestyle="--", alpha=0.4)
ax2.spines[["top", "right"]].set_visible(False)
plt.tight_layout()

plt.show()

