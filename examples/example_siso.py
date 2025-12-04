import numpy as np
import matplotlib.pyplot as plt

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks import  Step, LinearStateSpace

def main():
    # --- 1. Define system matrices (SISO example) ---
    A = np.array([[0., 0.25], [0.3, 0.91]])       # (2x2)
    B = np.array([[0.5], [0.3]])       # (2x1)
    C = np.array([[0., 1.0]])     # y = x


    # --- 2. Create blocks ---
    command = Step(
        name="command",
        value_before=np.array([[0.0]]),
        value_after=np.array([[1.0]]),
        t_step=0.5,
    )

    # Linear state-space system
    plant = LinearStateSpace(
        name="plant",
        A=A, B=B, C=C,
        x0=np.zeros((2, 1)),
    )


    # --- 3. Build the model ---
    model = Model(name="siso")
    model.add_block(command)
    model.add_block(plant)

    model.connect("command", "out", "plant", "u")


    # --- 4. Create the simulator ---
    dt = 0.01  # 10 ms
    sim = Simulator(model, dt=dt)

    # --- 5. Run simulation ---
    T = 2.0  # 2 seconds
    logs = sim.run(
        T=T,
        variables_to_log=[
            "command.outputs.out",
            "plant.outputs.x",
            "plant.outputs.y",
        ],
    )


    # --- 6. Inspect / print some results ---
    t = np.arange(0, T, dt)
    length = min(len(t), len(logs["plant.outputs.y"]))
    t = t[:length]

    u = np.array(logs["command.outputs.out"]).reshape(length, -1)
    x = np.array(logs["plant.outputs.x"]).reshape(length, -1)
    y = np.array(logs["plant.outputs.y"]).reshape(length, -1)


    plt.figure()
    plt.plot(t, u, label="u (step)")
    plt.plot(t, x[:, 0], label="x1 (plant)")
    plt.plot(t, y, label="x2=y (plant)")
    plt.legend()
    plt.grid(True)
    plt.xlabel("Time [s]")
    plt.show()

if __name__ == "__main__":
    main()
