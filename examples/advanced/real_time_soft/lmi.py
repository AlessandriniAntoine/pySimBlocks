import numpy as np
import cvxpy as cp
import control as ct


def get_lmi_controller(A, B, C):
    """Compute the LMI controller.
    """
    nx = A.shape[0]
    nu = B.shape[1]
    ny = C.shape[0]

    # # Define the decay factor and matrices for the LQR problem
    decay = 0.99
    Qy = 1e0 * np.diag(ny//2 * [1, 0.5])
    Q = C.T @ Qy @ C
    eig = max(abs(np.linalg.eigvals(Q)))
    Q = Q + 1e-3*eig * np.eye(nx)
    R = 1e3 * np.eye(nu)
    Q_inv = np.linalg.inv(Q)
    R_inv = np.linalg.inv(R)

    # Define the optimization variables
    X = cp.Variable((nx, nx), symmetric=True)
    Y = cp.Variable((nu, nx))
    delta = cp.Variable(nonneg=True)

    gamma_decay = cp.bmat([
        [-X, 1/decay * (A @ X - B @ Y).T],
        [1/decay * (A @ X - B @ Y), -X]
    ])
    gamma_lqr = cp.bmat([
        [-X, (A @ X - B @ Y).T, X, Y.T],
        [(A @ X - B @ Y), -X, np.zeros((nx, nx)), np.zeros((nx, nu))],
        [X, np.zeros((nx, nx)), -Q_inv, np.zeros((nx, nu))],
        [Y, np.zeros((nu, nx)), np.zeros((nu, nx)), -R_inv]
    ])

    matrix = [-X]
    matrix.append(gamma_decay)
    matrix.append(gamma_lqr)
    matrix.append(cp.bmat([[-delta * np.eye(nx), np.eye(nx)], [np.eye(nx), -X]]))
    constraints = [mat << -1e-5 * np.eye(mat.shape[0]) for mat in matrix]

    # obj = cp.Minimize(0)
    obj = cp.Minimize(delta)
    pb = cp.Problem(obj, constraints)
    pb.solve(solver="MOSEK")
    print(f"Problem status: {pb.status}")
    if pb.status != cp.OPTIMAL:
        raise Exception(f"Control problem not solved. Status: {pb.status}")

    P = np.linalg.inv(X.value)
    K = Y.value @ P
    # Feedforward gain
    C_ctr = C[[0, 1]]
    G = np.linalg.inv(C_ctr @ np.linalg.inv(np.eye(nx) - A + B @ K) @ B)
    
    return K, G

def get_lmi_observer(A, C):
    """Compute the LMI observer.
    """
    nx = A.shape[0]
    ny = C.shape[0]
    Q = 8e2 * np.eye(nx)  # State error cost
    R = 1e1 * np.eye(ny)  # noise cost
    L = ct.dlqr(A.T, C.T, Q, R)[0].T
    return L
