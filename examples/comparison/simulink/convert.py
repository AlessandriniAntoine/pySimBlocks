import csv
import numpy as np

filename = "simulation.csv"

# Lecture du CSV
with open(filename, "r") as f:
    reader = csv.reader(f)
    rows = list(reader)

# Titres
titles = rows[0]

# Données converties en float
data = np.array(rows[1:], dtype=float)

# Construction dynamique du dictionnaire pour savez
save_dict = {"titles": np.array(titles)}

for i, name in enumerate(titles):
    key = name.strip()

    # Optionnel : sécuriser le nom si nécessaire
    # key = key.replace(" ", "_").replace("-", "_")

    save_dict[key] = data[:, i]

# Sauvegarde
np.savez("simulation.npz", **save_dict)
