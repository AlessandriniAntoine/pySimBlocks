from numpy import array, dot

M = array([[1., 2., 0.], [-8., 3., 2.], [0., 1., 1.]])
P = M.T @ M
q = array([[3., 2., 3.]]) @ M
#
# from qpsolvers import solve_qp
# x = solve_qp(P, q, None, None, None, None, None, solver="clarabel")
# print(f"QP solution: x = {x}")
#
