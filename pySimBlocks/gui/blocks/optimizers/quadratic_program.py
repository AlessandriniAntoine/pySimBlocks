# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
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

from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta


class QuadraticProgramMeta(BlockMeta):

    def __init__(self):
        self.name = "QuadraticProgram"
        self.category = "optimizers"
        self.type = "quadratic_program"
        self.summary = "General time-varying quadratic program (QP) solver."
        self.description = (
            "Solves at each simulation step the quadratic program:\n"
            "$$\n"
            "\\begin{aligned}\n"
            "\\min_x \\quad & \\tfrac12 x^T P x + q^T x \\\\\n"
            "\\text{s.t.} \\quad\n"
            "& Gx \\le h \\\\\n"
            "& Ax = b \\\\\n"
            "& \\ell \\le x \\le u\n"
            "\\end{aligned}\n"
            "$$\n"
            "All problem data are provided as inputs and may vary with time.\n"
            "Inequality, equality, and bound constraints are optional."
        )

        self.parameters = [
            ParameterMeta(
                name="solver",
                type="string",
                autofill=True,
                default="clarabel",
                description="Name of the QP solver used by qpsolvers."
            )
        ]

        self.inputs = [
            PortMeta(
                name="P",
                display_as="P",
                shape=["n", "n"],
                description="Quadratic cost matrix (Hessian). Must be square and compatible with size."
            ),
            PortMeta(
                name="q",
                display_as="q",
                shape=["n"],
                description="Linear cost vector. Accepted shapes are (n,) or (n,1)."
            ),
            PortMeta(
                name="G",
                display_as="G",
                shape=["m", "n"],
                description="Inequality constraint matrix. Must be provided together with h."
            ),
            PortMeta(
                name="h",
                display_as="h",
                shape=["m"],
                description="Inequality constraint vector. Accepted shapes are (m,) or (m,1)."
            ),
            PortMeta(
                name="A",
                display_as="A",
                shape=["p", "n"],
                description="Equality constraint matrix. Must be provided together with b."
            ),
            PortMeta(
                name="b",
                display_as="b",
                shape=["p"],
                description="Equality constraint vector. Accepted shapes are (p,) or (p,1)."
            ),
            PortMeta(
                name="lb",
                display_as="lb",
                shape=["n"],
                description="Lower bound on decision variables. Accepted shapes are (n,) or (n,1)."
            ),
            PortMeta(
                name="ub",
                display_as="ub",
                shape=["n"],
                description="Upper bound on decision variables. Accepted shapes are (n,) or (n,1)."
            )
        ]

        self.outputs = [
            PortMeta(
                name="x",
                display_as="x",
                shape=["n", 1],
                description="Optimal solution of the quadratic program."
            ),
            PortMeta(
                name="status",
                display_as="status",
                shape=[1, 1],
                description="Solver status code:\n0 = optimal solution found,\n1 = problem infeasible,\n2 = solver or numerical error."
            ),
            PortMeta(
                name="cost",
                display_as="cost",
                shape=[1, 1],
                description="Optimal value of the quadratic cost function."
            )
        ]
