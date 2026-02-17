import numpy as np
import control as ct

A = np.array([[0.95, 0.1], [0, 0.98]])
B = np.array([[1], [1]])
C = np.array([[1., 0.]])

K = ct.place(A, B, [0.9, 0.91])
G = np.linalg.inv(C @ np.linalg.inv(np.eye(2) - A + B @ K) @ B)
