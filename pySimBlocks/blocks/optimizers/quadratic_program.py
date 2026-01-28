# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Antoine Alessandrini
# ******************************************************************************
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
#  for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ******************************************************************************
#  Authors: see Authors.txt
# ******************************************************************************

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
        solver: str
            QP solver name (default: "clarabel").

    I/O:
        Inputs:
            P: array (n,n)
                Quadratic cost matrix.
            q: array (n,) or (n,1)
                Linear cost vector.
            G: array (m,n) or None
                Inequality constraint matrix.
            h: array (m,) or (m,1) or None
                Inequality constraint vector.
            A: array (p,n) or None
                Equality constraint matrix.
            b: array (p,) or (p,1) or None
                Equality constraint vector.
            lb: array (n,) or (n,1) or None
                Lower bound on x. (No scalar broadcast.)
            ub: array (n,) or (n,1) or None
                Upper bound on x. (No scalar broadcast.)

        Outputs:
            x: array (n,1)
                Optimal solution (or zeros on failure).
            status: array (1,1)
                Solver status:
                    0 = optimal
                    1 = infeasible / no solution
                    2 = solver error
                    3 = input error
            cost: array (1,1)
                Optimal cost value (NaN on failure).
    """

    def __init__(self, name: str, solver: str = "clarabel"):
        super().__init__(name)

        self._size: int | None = None

        if solver not in available_solvers:
            raise ValueError(
                f"Solver '{solver}' is not available. Available solvers: {available_solvers}"
            )
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


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float):
        self.outputs["x"] = np.zeros((1, 1))
        self.outputs["status"] = np.array([[2]])
        self.outputs["cost"] = np.array([[np.nan]])

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        # --- fetch raw
        P_raw = self.inputs.get("P", None)
        q_raw = self.inputs.get("q", None)
        G_raw = self.inputs.get("G", None)
        h_raw = self.inputs.get("h", None)
        A_raw = self.inputs.get("A", None)
        b_raw = self.inputs.get("b", None)
        lb_raw = self.inputs.get("lb", None)
        ub_raw = self.inputs.get("ub", None)

        # --- normalize types/shapes (numpy)
        try:
            P = self._as_matrix(P_raw) if P_raw is not None else None
            q = self._as_vector(q_raw) if q_raw is not None else None

            G = self._as_matrix(G_raw) if G_raw is not None else None
            h = self._as_vector(h_raw) if h_raw is not None else None

            A = self._as_matrix(A_raw) if A_raw is not None else None
            b = self._as_vector(b_raw) if b_raw is not None else None

            lb = self._as_vector(lb_raw) if lb_raw is not None else None
            ub = self._as_vector(ub_raw) if ub_raw is not None else None

            self._check_needed_input(P, q, G, h, A, b)
            self._check_size_compatibility(P, q, G, h, A, b, lb, ub)

        except (ValueError, TypeError):
            self._set_failure(status=3)
            return

        # Ensure output placeholder x matches resolved size (even before solving)
        self._ensure_output_x_size()

        # --- build & solve
        try:
            problem = Problem(P, q, G, h, A, b, lb, ub)
            sol = solve_problem(problem, solver=self.solver)

            if sol is None or getattr(sol, "x", None) is None:
                self._set_failure(status=1)
                return

            x = np.asarray(sol.x, dtype=float).reshape(-1, 1)
            if x.shape != (self._size, 1):
                raise RuntimeError(
                    f"[{self.name}] Solver returned x with shape {x.shape}, expected ({self._size},1)."
                )

            # cost = 1/2 x^T P x + q^T x
            cost = 0.5 * float(x.T @ P @ x) + float(q.reshape(1, -1) @ x)

            self.outputs["x"] = x
            self.outputs["status"] = np.array([[0]])
            self.outputs["cost"] = np.array([[cost]])

        except Exception:
            self._set_failure(status=2)

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        pass


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    @staticmethod
    def _check_needed_input(P, q, G, h, A, b):
        if P is None:
            raise ValueError("Missing required QP input 'P'.")
        if q is None:
            raise ValueError("Missing required QP input 'q'.")

        # paired constraints
        if (G is None) != (h is None):
            raise ValueError("Inequality constraints G and h must both be provided or both be None.")
        if (A is None) != (b is None):
            raise ValueError("Equality constraints A and b must both be provided or both be None.")

    # ------------------------------------------------------------------
    @staticmethod
    def _as_matrix(value) -> np.ndarray:
        arr = np.asarray(value, dtype=float)
        if arr.ndim != 2:
            raise ValueError(f"Matrix input must be 2D. Got shape {arr.shape}.")
        return arr

    # ------------------------------------------------------------------
    @staticmethod
    def _as_vector(value) -> np.ndarray:
        """
        Convert input to a strict 1D vector (n,).
        Accepts:
            - (n,) -> ok
            - (n,1) -> flatten
        Rejects:
            - scalar
            - (1,1)
            - any other shape
        """
        arr = np.asarray(value, dtype=float)

        if arr.ndim == 1:
            return arr

        if arr.ndim == 2 and arr.shape[1] == 1:
            return arr[:, 0]

        raise ValueError(
            f"Vector input must be shape (n,) or (n,1). Got shape {arr.shape}."
        )

    # ------------------------------------------------------------------
    def _ensure_output_x_size(self) -> None:
        """
        Keep outputs['x'] consistent with resolved size if known.
        This prevents dimension-propagation issues when the solver fails.
        """
        size = self._size if self._size is not None else 1

        x = self.outputs.get("x", None)
        if x is None:
            self.outputs["x"] = np.zeros((size, 1))
            return

        x_arr = np.asarray(x)
        if x_arr.shape != (size, 1):
            self.outputs["x"] = np.zeros((size, 1))

    # ------------------------------------------------------------------
    def _set_failure(self, status: int):
        self.outputs["status"] = np.array([[status]])
        self.outputs["cost"] = np.array([[np.nan]])
        self._ensure_output_x_size()

    # ------------------------------------------------------------------
    def _check_size_compatibility(self, P, q, G, h, A, b, lb, ub):
        # P defines the size n
        n = P.shape[0]

        # Freeze size once known
        if self._size is None:
            self._size = n
        elif self._size != n:
            raise ValueError(
                f"[{self.name}] Inconsistent QP size across time steps. "
                f"Previous size: {self._size}, current size: {n}."
            )

        # P must be square
        if P.ndim != 2 or P.shape[1] != n:
            raise ValueError(f"[{self.name}] Input 'P' must be square, got shape {P.shape}.")

        # q must be (n,)
        if q.ndim != 1 or q.shape[0] != n:
            raise ValueError(
                f"[{self.name}] Input 'q' has shape {q.shape}. Must be (n,) with n={n}."
            )

        # Inequality constraints
        if G is not None:
            if h is None:
                raise ValueError(f"[{self.name}] Inequality constraints require both G and h.")
            if G.ndim != 2 or G.shape[1] != n:
                raise ValueError(
                    f"[{self.name}] Input 'G' has shape {G.shape}. Must be (m,n) with n={n}."
                )
            m = G.shape[0]
            if h.ndim != 1 or h.shape[0] != m:
                raise ValueError(
                    f"[{self.name}] Input 'h' has shape {h.shape}. Must be (m,) with m={m}."
                )
        else:
            if h is not None:
                raise ValueError(f"[{self.name}] Inequality constraints G and h must both be provided or both be None.")

        # Equality constraints
        if A is not None:
            if b is None:
                raise ValueError(f"[{self.name}] Equality constraints require both A and b.")
            if A.ndim != 2 or A.shape[1] != n:
                raise ValueError(
                    f"[{self.name}] Input 'A' has shape {A.shape}. Must be (p,n) with n={n}."
                )
            p = A.shape[0]
            if b.ndim != 1 or b.shape[0] != p:
                raise ValueError(
                    f"[{self.name}] Input 'b' has shape {b.shape}. Must be (p,) with p={p}."
                )
        else:
            if b is not None:
                raise ValueError(f"[{self.name}] Equality constraints A and b must both be provided or both be None.")

        # Bounds (no scalar broadcast)
        if lb is not None:
            if lb.ndim != 1 or lb.shape[0] != n:
                raise ValueError(
                    f"[{self.name}] Input 'lb' has shape {lb.shape}. Must be (n,) with n={n}."
                )
        if ub is not None:
            if ub.ndim != 1 or ub.shape[0] != n:
                raise ValueError(
                    f"[{self.name}] Input 'ub' has shape {ub.shape}. Must be (n,) with n={n}."
                )
