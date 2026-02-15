import numpy as np
import matplotlib.pyplot as plt

# Dimensions
r = 3      # number of vertices
nx = 4     # state dimension
nu = 1     # input dimension
ny = 2     # output dimension


# Create A_i matrices
A1 = np.array([
    [0.8, 0.1, 0.0, 0.0],
    [0.0, 0.7, 0.1, 0.0],
    [0.0, 0.0, 0.6, 0.1],
    [0.0, 0.0, 0.0, 0.5],
])

A2 = A1 + 0.05 * np.eye(nx)
A3 = A1 - 0.05 * np.eye(nx)

A = np.hstack([A1, A2, A3])


# Create B_i matrices
B1 = np.array([[1.0], [0.0], [0.0], [0.0]])
B2 = np.array([[0.5], [0.5], [0.0], [0.0]])
B3 = np.array([[0.2], [0.3], [0.3], [0.2]])

B = np.hstack([B1, B2, B3])


# Output matrix
C = np.array([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
])


