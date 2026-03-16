# Installation

`pySimBlocks` requires Python 3.10 or newer.

## From PyPI

```bash
pip install pySimBlocks
```

## From GitHub

```bash
pip install git+https://github.com/AlessandriniAntoine/pySimBlocks
```

## Local Development Install

```bash
git clone https://github.com/AlessandriniAntoine/pySimBlocks.git
cd pySimBlocks
pip install .
```

## Documentation build

To build the documentation locally from the `docs` directory:

```bash
pip install pySimBlocks[docs]
make html
```

## Optional dependencies

### Examples

Some examples require additional dependencies. You can install them with:

```bash
pip install pySimBlocks[examples]
```

### Testing
To run the tests, you need to install the testing dependencies:

```bash
pip install pySimBlocks[tests]
```
