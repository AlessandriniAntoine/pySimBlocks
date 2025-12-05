import numpy as np

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks import Sinusoidal, DiscreteDerivator


dt = 0.1
T = 2.0
w = 2.0  # rad/s


# ============================================================
# Reference discrete derivative functions
# ============================================================

def ref(u, dt):
    """
    y[k] = (u[k] - u[k-1]) / dt
    with y[0] = 0
    """
    N = len(u)
    y = np.zeros((N, 1))
    for k in range(1, N):
        y[k] = (u[k] - u[k-1]) / dt
    return y



# ============================================================
# Generic test runner
# ============================================================

def run_test():
    """
    Generic test function:
    - Build model: sinusoidal → derivator(method)
    """

    # Input: sinusoid u(t) = sin(w t)
    src = Sinusoidal(
        "u",
        amplitude=1.0,
        frequency=w/(2*np.pi),
        phase=0.0,
        offset=0.0
    )

    deriv = DiscreteDerivator("deriv")

    model = Model("test_deriv")
    model.add_block(src)
    model.add_block(deriv)
    model.connect("u", "out", "deriv", "in")

    sim = Simulator(model, dt=dt)
    logs = sim.run(T=T, variables_to_log=["u.outputs.out", "deriv.outputs.out"])

    u = np.array(logs["u.outputs.out"]).reshape(-1, 1)
    y = np.array(logs["deriv.outputs.out"]).reshape(-1, 1)
    t = np.arange(0, len(y)) * dt

    # Compute discrete reference
    y_ref = ref(u, dt)

    # Compute numerical error
    err = np.linalg.norm(y - y_ref)

    print(f"Error = {err}")
    print(f"y_ref (first 5 samples): {y_ref[:5].flatten()}")
    print(f"y (first 5 samples): {y[:5].flatten()}")

    assert err < 1e-12, f"Discrete derivative mismatch !"

# ============================================================
# Main execution
# ============================================================

if __name__ == "__main__":
    run_test()
    print("All DiscreteDerivator tests passed.")
