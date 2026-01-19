# pySimBlocks

Simulink python project

pySimBlocks is a lightweight and extensible environment for building, configuring, and executing block-diagram models—similar to Simulink—directly in Python, featuring a PySide6-based graphical editor, a discrete-time simulation engine, and automatic project generation from YAML configurations.

## How to

- Option 1 - Install from GitHub
```
pip install git+https://github.com/AlessandriniAntoine/pySimBlocks
```

- Option 2 - Clone the repository and install locally
```
git clone https://github.com/AlessandriniAntoine/pySimBlocks.git
cd pySimBlocks
pip install .
```

### Run GUI application
```
pysimblocks
```

## Documentation

Si utilisation variables workspace ecrire: `= var_name`

pour les nom inputs des blocks ou l'utilisateur specifie une valeur. Il faut respecter cette syntaxe:
Inputs:
    Dynamic — specified by `input_keys` 
pareil pour les outputs:
Outputs:
    Dynamic — specified by `output_keys`
