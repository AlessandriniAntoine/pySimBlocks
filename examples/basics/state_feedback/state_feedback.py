import numpy as np
import matplotlib.pyplot as plt
import control as ct

from pySimBlocks import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources import  Step
from pySimBlocks.blocks.controllers import  StateFeedback
from pySimBlocks.blocks.systems import  LinearStateSpace


def main():
    # --- 1. Define system matrices (SISO example) ---
    A = np.array([[0.95, 0.1], [0, 0.98]])
    B = np.array([[1], [1]])
    C = np.array([[1., 0.]])

    K = ct.place(A, B, [0.9, 0.91])
    G = np.linalg.inv(C @ np.linalg.inv(np.eye(2) - A + B @ K) @ B)

    # --- 2. Create blocks ---
    # Step : 0 -> 1 at start_time = 0.5 s
    ref = Step(
        name="ref",
        value_before=np.array([[0.0]]),
        value_after=np.array([[1.0]]),
        start_time=0.5,
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
    T = 2.0  # 2 seconds
    sim_cfg = SimulationConfig(dt, T)
    sim = Simulator(model, sim_cfg)

    # --- 5. Run simulation ---
    logs = sim.run(logging=[
            "ref.outputs.out",
            "controller.outputs.u",
            "plant.outputs.x",
            "plant.outputs.y",
        ],
    )

    # --- 6. Inspect / print some results ---
    length = len(logs["plant.outputs.y"])

    t = sim.get_data("time")
    r = sim.get_data("ref.outputs.out").squeeze()
    y = sim.get_data("plant.outputs.y").squeeze()
    x = sim.get_data("plant.outputs.x").squeeze()
    u = sim.get_data("controller.outputs.u").squeeze()

    plt.figure()
    plt.step(t, r, label="ref (step)", where="post")
    plt.step(t, y, label="y (plant output)", where="post")
    plt.legend()
    plt.grid(True)
    plt.xlabel("Time [s]")
    plt.title("Reference tracking")


    plt.figure()
    plt.step(t, u, label="u = gain(ref)", where="post")
    plt.legend()
    plt.grid(True)
    plt.xlabel("Time [s]")
    plt.title("Control input")

    plt.figure()
    plt.step(t, x[:, 0], label="x1 (state 1)", where="post")
    plt.step(t, x[:, 1], label="x2 (state 2)", where="post")
    plt.legend()
    plt.grid(True)
    plt.xlabel("Time [s]")
    plt.title("States evolution")

    plt.show()


if __name__ == "__main__":
    main()
