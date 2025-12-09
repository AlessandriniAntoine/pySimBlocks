import csv
import numpy as np

filename = "simulation.csv"

with open(filename, "r") as f:
    reader = csv.reader(f)
    rows = list(reader)

# Première ligne = titres
titles = rows[0]

# Données converties en float
data = np.array(rows[1:], dtype=float)

np.savez("simulation.npz", titles=titles,
    time=data[:,0],
    uol=data[:,1],
    wol=data[:,2],
    uol_block=data[:,3],
    wol_block=data[:,4],
    upi=data[:,5],
    wpi=data[:,6],
    upi_block=data[:,7],
    wpi_block=data[:,8],
    upid=data[:,9],
    wpid=data[:,10],
    upid_block=data[:,11],
    wpid_block=data[:,12],
    r=data[:,13]
)
