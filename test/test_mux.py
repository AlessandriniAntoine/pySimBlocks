import numpy as np

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks import Constant, Mux


def test_mux_basic():
    # s
    a = Constant("a", value=np.array([[1.0]]))         # shape (1,1)
    b = Constant("b", value=np.array([[2.0], [3.0]]))  # shape (2,1)
    c = Constant("c", value=np.array([[4.0]]))         # shape (1,1)

    mux = Mux("mux", num_inputs=3)

    # Build model
    model = Model("mux_test")
    model.add_block(a)
    model.add_block(b)
    model.add_block(c)
    model.add_block(mux)

    model.connect("a", "out", "mux", "in1")
    model.connect("b", "out", "mux", "in2")
    model.connect("c", "out", "mux", "in3")

    sim = Simulator(model, dt=0.1)

    logs = sim.run(
        T=0.1,
        variables_to_log=["mux.outputs.out"]
    )

    y = np.array(logs["mux.outputs.out"][-1]).reshape(-1, 1)

    expected = np.array([[1.0], [2.0], [3.0], [4.0]])

    err = np.linalg.norm(y - expected)
    assert err < 1e-12, f"Mux output incorrect: got {y.flatten()}, expected {expected.flatten()}"


if __name__ == "__main__":
    test_mux_basic()
    print("test_mux_basic passed.")
