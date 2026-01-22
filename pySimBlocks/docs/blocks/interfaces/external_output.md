# External Output Block

## Description

The External Output block represents a data output point in a simulation model. It allows the model to send signals to an external environment during simulation. The block outputs the value of the internal signal at each simulation time step.

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `in` | Model data signal $u$. |

---

## Outputs

| Port | Description |
|------|------------|
| `out` | External data signal. |

---

## Notes

- The External Output block is **stateless**.

© 2026 The pySimBlocks Authors – Licensed under LGPL-3.0-or-later
