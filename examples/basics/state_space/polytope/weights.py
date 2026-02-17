import numpy as np


def get_weights(t, dt, c):
    w1 = np.clip(0.4 + 0.2 * np.sin(0.5 * t) + c, 0.0, 1.0)
    w2 = np.clip(0.3 + 0.1 * np.cos(0.3 * t), 0.0, 1-w1)
    w3 = 1.0 - w1 - w2
    w3 = np.clip(w3, 0.0, 1.0)

    val = np.array([w1, w2, w3]).reshape(-1, 1)
    return {"w": val}

