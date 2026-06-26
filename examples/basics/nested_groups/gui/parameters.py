import numpy as np
import control as ct

# 3-state coupled dynamics to generate richer state trajectories for plotting.
A = np.array([
    [0.95, 0.10, 0.00],
    [0.00, 0.97, 0.08],
    [0.00, 0.00, 0.93],
])
B = np.array([[1.0], [0.7], [0.4]])
C = np.array([[1.0, 0.0, 0.0]])

K = ct.place(A, B, [0.86, 0.88, 0.90])
G = np.linalg.inv(C @ np.linalg.inv(np.eye(3) - A + B @ K) @ B)
