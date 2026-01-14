# Sum Block

## Description

The **Sum** block computes a weighted sum of multiple input signals.

It implements:

$$ y = s_1 u_1 + s_2 u_2 + \dots + s_N u_N $$

where each coefficient $ s_i $ is either +1 or −1.

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `signs` | string | Sequence of '+' and '−' characters defining the sign for each input. | False |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |


---

## Inputs

| Port | Description |
|------|------------|
| `in1 … inN` | Input signals to be summed. All inputs must have identical dimensions or scalar. |

---

## Outputs

| Port | Description |
|------|------------|
| `out` | Weighted sum of all input signals. |

---

## Notes

- The Sum block has no internal state.
- The number of input ports is determined by the length of `signs`.
- This block is equivalent to the Simulink **Sum** block.
