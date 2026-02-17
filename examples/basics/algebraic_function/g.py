def g(t, dt, u1, u2):
    y1 = 3 * u1
    y2 = 2 * u2 + dt
    return {
        "y1": y1,
        "y2": y2
    }
