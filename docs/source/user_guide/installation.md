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

To also build the documentation locally:

```bash
pip install pySimBlocks[docs]
cd docs
make html
```

The HTML output will be in `docs/_build/html/`.

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

## Troubleshooting

### Windows: installation fails with "No such file or directory"

This error is caused by Windows' 260-character path limit (MAX_PATH). It typically
affects Python installed from the Microsoft Store, which uses a long AppData path.

**Fix:** enable long paths in PowerShell (administrator):
```powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
    -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

Then restart and reinstall. If the problem persists, reinstall Python from
[python.org](https://www.python.org/downloads/windows/) instead of the Microsoft Store.
