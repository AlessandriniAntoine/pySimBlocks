import numpy as np
import control as ct

A = np.array([[0.9, 0.8], [0, 0.95]])
B = np.array([[0.], [0.5]])
C = np.array([[1, 0]])

vp = [0.8, 0.85]
K = ct.place(A, B, vp)
G = np.linalg.inv(C @ np.linalg.inv(np.eye(2) - A + B @ K) @ B)
