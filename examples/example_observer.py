import numpy as np
import matplotlib.pyplot as plt

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks import Constant, LinearStateSpace, Luenberger


def main():
    # System
    A = np.array([[0.9]])
    B = np.array([[1.0]])
    C = np.array([[1.0]])

    # Observer gain L
    L = np.array([[0.5]])

    # True plant
    plant = LinearStateSpace("plant", A=A, B=B, C=C, x0=np.array([[0.0]]))

    # Command (constant)
    u_val = np.array([[1.0]])
    u_src = Constant("u", value=u_val)

    # Observer
    obs = Luenberger(
        name="observer",
        A=A, B=B, C=C, L=L,
        x0=np.array([[-2.0]])
    )

    # Build model
    model = Model("observer_test")
    model.add_block(u_src)
    model.add_block(plant)
    model.add_block(obs)

    model.connect("u", "out", "plant", "u")
    model.connect("u", "out", "observer", "u")
    model.connect("plant", "y", "observer", "y")

    dt = 0.1
    sim = Simulator(model, dt=dt)

    T = 10.
    logs = sim.run(
        T=T,
        variables_to_log=[
            "plant.outputs.x",
            "observer.outputs.x_hat",
        ]
    )

    # Extract logs
    length = len(logs["plant.outputs.x"])
    t = np.arange(0, T, dt)
    x_true = np.array(logs["plant.outputs.x"]).reshape(length, -1)
    x_hat = np.array(logs["observer.outputs.x_hat"]).reshape(length, -1)

    # The observer should track the state with low error after a few steps
    error = np.linalg.norm(x_true[-1] - x_hat[-1])
    print(f"Final estimation error: {error}")


    plt.figure()
    plt.plot(t, x_true, label="True State x")
    plt.plot(t, x_hat, label="Estimated State x_hat", linestyle='--')
    plt.xlabel("Time [s]")
    plt.ylabel("State Value")
    plt.title("Luenberger Observer State Estimation")
    plt.legend()
    plt.grid()
    plt.show()


if __name__ == "__main__":
    main()
