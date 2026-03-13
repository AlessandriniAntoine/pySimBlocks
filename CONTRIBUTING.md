# Contributing to pySimBlocks

Thank you for your interest in contributing to **pySimBlocks**.
pySimBlocks is a research-oriented simulation framework for discrete-time
block-diagram systems with a graphical editor and YAML project format.

Contributions are welcome in the following areas:

- Simulation engine
- GUI editor
- New blocks
- Documentation
- Tests
- Performance improvements

---

## Repository architecture

```
.
├── docs/               # User guides and block documentation
├── examples/           # Usage examples
├── pySimBlocks/
│   ├── blocks/         # Block implementations (operators, controllers, sources, …)
│   ├── core/           # Simulation engine (Model, Simulator, Block base class, …)
│   ├── gui/            # PySide6 graphical editor
│   ├── project/        # YAML project loading and code generation
│   ├── real_time/      # Real-time execution
│   └── tools/          # CLI and block registry utilities
├── tests/              # Test suite
├── pyproject.toml
└── README.md
```

---

## Docstring format

pySimBlocks uses **Google-style docstrings**. Every public class and method must have one.

### Class

```python
class MyBlock(Block):
    """One-line summary ending with a period.

    Optional longer description: what the block computes, its mathematical
    formulation, and any important behavioural notes.

    Attributes:
        gain: Scalar gain applied to the input.
        sample_time: Sampling period, or None to use the global dt.
    """
```

### Method

```python
def output_update(self, t: float, dt: float) -> None:
    """Compute output y[k] = gain * u[k].

    Args:
        t: Current simulation time in seconds.
        dt: Current time step in seconds.
    """
```

**Rules:**
- Always include `Args` when the method takes parameters beyond `self`.
- Include `Returns` when the return value is not `None` and not obvious.
- Include `Raises` for exceptions the caller should handle.
- Do **not** repeat type information already present in the signature.
- Private methods (`_foo`): a one-line comment is sufficient.

---

## Coding style

Follow standard Python conventions:

- Python ≥ 3.10
- PEP 8 formatting
- Descriptive variable names

### Naming conventions

| Element | Convention | Example |
|---|---|---|
| Block class | `PascalCase` | `DiscreteIntegrator`, `Gain` |
| Block file | `snake_case` | `discrete_integrator.py`, `gain.py` |
| GUI metadata class | `PascalCase` + `Meta` suffix | `DiscreteIntegratorMeta`, `GainMeta` |
| GUI metadata file | same as block file | `discrete_integrator.py` |
| Doc file | same as block file | `discrete_integrator.md` |
| Test file | `test_` + block file | `test_discrete_integrator.py` |
| Test functions | `test_<block>_<what>_<expected>` | `test_gain_negative_input_inverts_sign` |
| Block `type` key (yaml/GUI) | `snake_case` | `"discrete_integrator"` |
| Input/output port names | `snake_case` | `"in"`, `"out"`, `"error"` |
| State keys | `snake_case` | `"x"`, `"x_i"`, `"prev_e"` |

---

## Running tests

```bash
pytest tests/
```

---

© 2026 Université de Lille & INRIA
Licensed under LGPL-3.0-or-later
