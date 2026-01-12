import numpy as np 

def f(t, dt, x, u):
    """
    Non-linear state-space function for a discrete-time system.

    Parameters:
    t : float
        Current time.
    dt : float
        Time step.
    x : ndarray
        Current state vector.
    u : ndarray
        Current input vector.

    Returns:
    x_next : ndarray
        Next state vector after applying the non-linear dynamics.
    """
    x_next = np.zeros_like(x)
    x_next[0] = x[0] + dt * (x[1] +  np.sin(x[0]) + u[0]**2)
    x_next[1] = x[1] + dt * (-x[0]**3 - 0.5 * x[1])
    
    return x_next


def g(t, dt, x):
    """
    Non-linear output function for a discrete-time system.

    Parameters:
    t : float
        Current time.
    dt : float
        Time step.
    x : ndarray
        Current state vector.

    Returns:
    y : ndarray
        Output vector after applying the non-linear output function.
    """
    y = np.zeros((1, 1))
    y[0] = x[0]**2 + np.cos(x[1])
    
    return {"y": y}
