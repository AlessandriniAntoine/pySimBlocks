import numpy as np
import matplotlib.pyplot as plt
import control as ct

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks import  Step, StateFeedback, LinearStateSpace, Gain


def main():
    # --- 1. Define system matrices (SISO example) ---
    A = np.array([[0.95, 0.1], [0, 0.98]])
    B = np.array([[1], [1]])
    C = np.array([[1., 0.]])

    K = ct.place(A, B, [0.9, 0.91])
    G = np.linalg.inv(C @ np.linalg.inv(np.eye(2) - A + B @ K) @ B)

    # --- 2. Create blocks ---
    # Step : 0 -> 1 at t_step = 0.5 s
    ref = Step(
        name="ref",
        value_before=np.array([[0.0]]),
        value_after=np.array([[1.0]]),
        t_step=0.5,
    )

    # State feedback controller
    controller = StateFeedback(name="controller", K=K, G=G)

    # Linear state-space system
    plant = LinearStateSpace(
        name="plant",
        A=A, B=B, C=C,
        x0=np.array([[0.], [0.]]),
    )

    # --- 3. Build the model ---
    model = Model(name="state_feedback_control")
    model.add_block(ref)
    model.add_block(controller)
    model.add_block(plant)

    # Connect:
    model.connect("ref", "out", "controller", "r")
    model.connect("controller", "u", "plant", "u")
    model.connect("plant", "x", "controller", "x")

    # --- 4. Create the simulator ---
    dt = 0.01  # 10 ms
    sim = Simulator(model, dt=dt)

    # --- 5. Run simulation ---
    T = 2.0  # 2 seconds
    logs = sim.run(
        T=T,
        variables_to_log=[
            "ref.outputs.out",
            "controller.outputs.u",
            "plant.outputs.x",
            "plant.outputs.y",
        ],
    )


    # --- 6. Inspect / print some results ---
    t = np.arange(0, T, dt)
    length = min(len(t), len(logs["plant.outputs.y"]))
    t = t[:length]

    r = np.array(logs["ref.outputs.out"]).reshape(length, -1)
    y = np.array(logs["plant.outputs.y"]).reshape(length, -1)
    x = np.array(logs["plant.outputs.x"]).reshape(length, -1)
    u = np.array(logs["controller.outputs.u"]).reshape(length, -1)

    plt.figure()
    plt.plot(t, r, label="ref (step)")
    plt.plot(t, y, label="y (plant output)")
    plt.legend()
    plt.grid(True)
    plt.xlabel("Time [s]")
    plt.title("Reference tracking")


    plt.figure()
    plt.plot(t, u, label="u = gain(ref)")
    plt.legend()
    plt.grid(True)
    plt.xlabel("Time [s]")
    plt.title("Control input")

    plt.figure()
    plt.plot(t, x[:, 0], label="x1 (state 1)")
    plt.plot(t, x[:, 1], label="x2 (state 2)")
    plt.legend()
    plt.grid(True)
    plt.xlabel("Time [s]")
    plt.title("States evolution")

    plt.show()


if __name__ == "__main__":
    main()
