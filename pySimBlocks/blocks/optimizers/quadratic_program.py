import numpy as np
from qpsolvers import Problem, solve_problem, available_solvers

from pySimBlocks.core.block import Block


class QuadraticProgram(Block):
    """
    General time-varying quadratic program solver.

    Summary:
        Solves at each time step the quadratic program:

            minimize    1/2 x^T P x + q^T x
            subject to  G x <= h
                        A x = b
                        lb <= x <= ub

        All problem data are provided as inputs and may vary with time.
        Constraints may be omitted by providing None.

    Parameters:
        name: str
            Block name.
        size: int
            Problem size (number of decision variables).
        solver: str
            QP solver name (default: "clarabel").

    I/O:
        Inputs:
            P: array (n,n)
                Quadratic cost matrix.
            q: array (n,1)
                Linear cost vector.
            G: array (m,n) or None
                Inequality constraint matrix.
            h: array (m,1) or None
                Inequality constraint vector.
            A: array (p,n) or None
                Equality constraint matrix.
            b: array (p,1) or None
                Equality constraint vector.
            lb: array (n,1) or None
                Lower bound on x.
            ub: array (n,1) or None
                Upper bound on x.

        Outputs:
            x: array (n,1)
                Optimal solution.
            status: array (1,1)
                Solver status:
                    0 = optimal
                    1 = infeasible
                    2 = solver error
            cost: array (1,1)
                Optimal cost value.
    """

    def __init__(self, name: str, size: int, solver: str = "clarabel"):
        super().__init__(name)

        self.size = size

        if solver not in available_solvers():
            raise ValueError(f"Solver '{solver}' is not available. Available solvers: {available_solvers()}")
        self.solver = solver


        self.inputs = {
            "P": None,
            "q": None,
            "G": None,
            "h": None,
            "A": None,
            "b": None,
            "lb": None,
            "ub": None,
        }

        self.outputs = {
            "x": None,
            "status": None,
            "cost": None,
        }

        self.state = {}
        self.next_state = {}

    # ------------------------------------------------------------------
    def initialize(self, t0):
        self.outputs["x"] = np.zeros((self.size, 1))
        self.outputs["status"] = np.array([[2]])
        self.outputs["cost"] = np.array([[np.nan]])

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        P = self.inputs.get("P", None)
        q = self.inputs.get("q", None)
        G = self.inputs.get("G", None)
        h = self.inputs.get("h", None)
        A = self.inputs.get("A", None)
        b = self.inputs.get("b", None)
        lb = self.inputs.get("lb", None)
        ub = self.inputs.get("ub", None)

        self._check_needed_input(P, q, G, h, A, b)
        self._check_size_compatibility(P, q, G, h, A, b, lb, ub, self.size)

        P = self._as_matrix(P)
        q = self._as_list(q)

        G = self._as_matrix(G) if G is not None else None
        h = self._as_list(h) if h is not None else None

        A = self._as_matrix(A) if A is not None else None
        b = self._as_list(b) if b is not None else None

        lb = self._as_list(lb) if lb is not None else None
        ub = self._as_list(ub) if ub is not None else None

        try:
            problem = Problem(P, q, G, h, A, b, lb, ub)
            sol = solve_problem(problem, solver=self.solver)

            if sol is None:
                self._set_failure(status=1)
                return

            x = sol.reshape(-1, 1)

            cost = 0.5 * float(x.T @ P @ x + q.reshape(-1,1).T @ x)

            self.outputs["x"] = x
            self.outputs["status"] = np.array([[0]])
            self.outputs["cost"] = np.array([[cost]])

        except Exception:
            self._set_failure(status=2)

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        pass

    # ------------------------------------------------------------------
    def _set_failure(self, status: int):
        self.outputs["status"] = np.array([[status]])
        self.outputs["cost"] = np.array([[np.nan]])

        if self.outputs["x"] is None:
            self.outputs["x"] = np.zeros((self.size, 1))

    # ------------------------------------------------------------------
    @staticmethod
    def _check_size_compatibility(P, q, G, h, A, b, lb, ub, size):
        n = P.shape[0]
        if P.ndim != 2 or P.shape[1] != n or n != size:
            raise RuntimeError("Input 'P' must be square and compatible with problem size.")

        if not (
            (q.ndim == 1 and q.shape[0] == size) or
            (q.ndim == 2 and q.shape[1] == 1 and q.shape[0] == size)
            ):
            raise RuntimeError("Input 'q' must be a vector of length compatible with problem size.")

        if G is not None:
            m, n = G.shape[0], G.shape[1]
            if G.ndim != 2 or n != size:
                raise RuntimeError("Input 'G' must be 2d matrix with number of columns compatible with problem size.")
            if not (
                (h.ndim == 1 and h.shape[0] == m) or
                (h.ndim == 2 and h.shape[1] == 1 and h.shape[0] == m)
            ):
                raise RuntimeError("Input 'h' must be a vector of length compatible with 'G'.")

        if A is not None:
            m, n = A.shape[0], A.shape[1]
            if A.ndim != 2 or n != size:
                raise RuntimeError("Input 'A' must be 2d matrix with number of columns compatible with problem size.")
            if not (
                (b.ndim == 1 and b.shape[0] == m) or
                (b.ndim == 2 and b.shape[1] == 1 and b.shape[0] == m)
            ):
                raise RuntimeError("Input 'b' must be a column vector compatible with 'A'.")

        if lb is not None:
            if not (
                (lb.ndim == 1 and lb.shape[0] == size) or
                (lb.ndim == 2 and lb.shape[1] == 1 and lb.shape[0] == size)
            ):
                raise RuntimeError("Input 'lb' has incompatible size with problem size.")
        if ub is not None:
            if not (
                (ub.ndim == 1 and ub.shape[0] == size) or
                (ub.ndim == 2 and ub.shape[1] == 1 and ub.shape[0] == size)
            ):
                raise RuntimeError("Input 'ub' has incompatible size with problem size.")

    # ------------------------------------------------------------------
    @staticmethod
    def _check_needed_input(P, q, G, h, A, b):

        if P is None:
            raise RuntimeError("Missing required QP input 'P'.")

        if q is None:
            raise RuntimeError("Missing required QP input 'q'.")

        if (G is None) != (h is None):
            raise RuntimeError("Inequality constraints G and h must both be provided or both be None.")

        if (A is None) != (b is None):
            raise RuntimeError("Equality constraints A and b must both be provided or both be None.")


    # ------------------------------------------------------------------
    @staticmethod
    def _as_matrix(value):
        arr = np.asarray(value, dtype=float)
        if arr.ndim != 2:
            raise ValueError("Matrix input must be 2D.")
        return arr

    # ------------------------------------------------------------------
    @staticmethod
    def _as_list(value):
        arr = np.asarray(value, dtype=float)
        if arr.ndim == 1:
            return arr.flatten()
        if arr.ndim == 2 and arr.shape[1] == 1:
            return arr.flatten()
        raise ValueError("Vector input must be shape (n,1) or (n,).")

