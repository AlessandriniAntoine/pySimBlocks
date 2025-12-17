# Sum Block

## Description

The **Sum** block computes a weighted sum of multiple input signals.

It implements:

$$ y = s_1 u_1 + s_2 u_2 + \dots + s_N u_N $$

where each coefficient \( s_i \) is either +1 or −1.

---

## Parameters

| Name | Description |
|------|------------|
| `num_inputs` | Number of input ports (default: 2). |
| `signs` | List of +1 or −1 coefficients applied to each input. |
| `sample_time` | Optional block sample time. |

If `signs` is not provided, all inputs are summed with a +1 coefficient.

---

## Inputs

| Port | Description |
|------|------------|
| `in1 … inN` | Input signals to be summed. All inputs must have identical dimensions. |

---

## Outputs

| Port | Description |
|------|------------|
| `out` | Weighted sum of all input signals. |

---

## Notes

- The Sum block has no internal state.
- The number of input ports is determined by `num_inputs` or the length of `signs`.
- This block is equivalent to the Simulink **Sum** block.
