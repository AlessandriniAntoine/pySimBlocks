import csv
import numpy as np

t = np.arange(0, 10, 0.1)
y = np.sin(t)
y = y.reshape(-1, 1)

np.savez('data.npz', time=t, y=y)

np.save('data.npy', y)

with open('data.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['time', 'y'])  # Write header
    for t_val, y_val in zip(t, y):
        writer.writerow([t_val, y_val[0]])  # Write each row of data
