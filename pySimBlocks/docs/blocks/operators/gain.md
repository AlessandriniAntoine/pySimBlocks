# Gain Block

## Description

The **Gain** block applies a static linear transformation to its input signal.

It computes:

$$ 
y = K \cdot u 
$$

where:
- $ u $ is the input signal,
- $ K $ is the gain,
- $ y $ is the output signal.

---

## Gain definition

The gain $ K $ can take several forms:

- **Scalar**: Multiplies the entire input signal by a constant.

- **Vector**: Applies an element-wise gain to a scalar input.

- **Matrix**: Applies a full linear transformation between input and output vectors.

---

## Parameters

| Name        | Type | Description | Optional |
|------------|-------------|-------------|-------------|
| `gain`     | scalar, vector, or matrix | Gain value(s) to apply. Can be a scalar, vector, or matrix depending on the desired transformation. | False |
| `sample_time` | float | Block sample time. If omitted, the global simulation time step is used. | True |

---

## Inputs

| Port | Description |
|------|------------|
| `in` | Input signal $ u $. |

---

## Outputs

| Port | Description |
|------|------------|
| `out` | Output signal $ y = K \cdot u $. |

---

## Notes

- The Gain block is **stateless**.
- Dimension mismatches between the gain and the input signal raise an error.
- This block is equivalent to the Simulink **Gain** block.
