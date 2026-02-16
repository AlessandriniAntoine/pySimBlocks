# FileSource Block

## Description

The FileSource block loads a sequence of numeric samples from a file and outputs one sample per simulation step.

Supported file formats:
- `npz`
- `npy`
- `csv`

---

## Parameters

| Name | Type | Description | Optional |
|------|------|-------------|----------|
| `file_path` | str | Path to source file. | False |
| `key` | str | Mandatory for `*.npz` (array key) and `*.csv` (column name). Unused for `*.npy`. | True |
| `repeat` | bool | End-of-file behavior. If `false`, outputs zeros after the last sample. If `true`, restarts from the first sample. | True (default: `False`) |
| `use_time` | bool | If `true` (only for `*.npz` and `*.csv`), uses a `time` signal and applies ZOH: at time `t`, output sample at largest index `i` such that `T[i] <= t`. | True (default: `False`) |
| `sample_time` | float | Block sample time. If omitted, global simulation step is used. | True |

---

## Inputs

None.

---

## Outputs

| Port | Description |
|------|-------------|
| `out` | Current sample as a column vector. |

---

## Notes

- File format is inferred from `file_path` extension (`.npz`, `.npy`, `.csv`).
- `npz`: loaded array must be 1D or 2D.
- `npy`: loaded array must be 1D or 2D.
- `csv`: `key` selects one named numeric column, producing shape `(1,1)` at each step.
- With `use_time=true`, `time` must exist and be strictly increasing.
  - `npz`: requires key `time`.
  - `csv`: requires column `time`.

---
© 2026 Université de Lille & INRIA - Licensed under LGPL-3.0-or-later
