# pySimBlocks — Benchmarks

Three benchmarks to measure and characterize the performance of the simulation engine.
Each benchmark is self-contained and can be run independently.

---

## bench_01_minimal_loop — Pure overhead

**Model:** first-order low-pass filter (5 blocks, scalar, 1 feedback loop)  
**Duration:** 100,000 steps, dt = 0.1 s

Isolates the irreducible cost of the simulation loop (scheduling, propagation, commit_state) without numerical computation dominating. Serves as a baseline: if this benchmark is slow, the bottleneck is in the engine core itself.

**Comparison:** pySimBlocks · PathSim · bdsim · Simulink

---

## bench_02_multi_feedback — Propagation and feedback stress test

**Model:** 10 blocks (gains, sums, discrete integrator), 2 nested feedback loops, 13 connections, vector signals  
**Duration:** 100,000 steps, dt = 0.001 s

Specifically targets the cost of inter-block data exchanges (`_propagate_from`, input/output dictionary accesses) in a model with multiple simultaneous feedbacks. Execution time was found to be insensitive to vector size (tested from 1 to 100) — the dominant cost is therefore structural (Python overhead per time step), not numerical.

**Comparison:** pySimBlocks · PathSim · Simulink

---

## bench_03_scaling — Engine scaling with number of blocks

**Model:** N cells in cascade, generated programmatically. Each cell contains a feedforward gain, a sum, a dynamic block (discrete integrator and delay alternating), a local feedback gain, and a coupling gain to the next cell — **5N blocks** and **~5N connections** in total.  
**Duration:** 100,000 steps, dt = 0.001 s · points: N ∈ {5, 10, 20, 50, 100} cells (25 to 500 blocks)

Characterizes how execution time scales with model size. **Linear scaling** (constant cost per step per block) indicates the engine handles each block independently and that execution order is properly cached. **Superlinear scaling** would reveal an architectural issue — typically execution order being recomputed or the dependency graph being rebuilt at each step.

**Comparison:** pySimBlocks only (scaling curve before/after optimization)
