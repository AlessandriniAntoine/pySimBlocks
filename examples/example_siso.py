import numpy as np
import matplotlib.pyplot as plt

from pySimBlocks import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import LinearStateSpace

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
        start_time=0.5,
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
    T = 2.0  # 2 seconds
    sim_cfg = SimulationConfig(dt, T)
    sim = Simulator(model, sim_cfg)

    # --- 5. Run simulation ---
    logs = sim.run(logging=[
            "command.outputs.out",
            "plant.outputs.x",
            "plant.outputs.y",
        ],
    )


    # --- 6. Inspect / print some results ---
    length = len(logs["plant.outputs.y"])

    t = np.array(logs["time"])
    u = np.array(logs["command.outputs.out"]).reshape(length, -1)
    x = np.array(logs["plant.outputs.x"]).reshape(length, -1)
    y = np.array(logs["plant.outputs.y"]).reshape(length, -1)


    plt.figure()
    plt.step(t, u, label="u (step)", where="post")
    plt.step(t, x[:, 0], label="x1 (plant)", where="post")
    plt.step(t, y, label="x2=y (plant)", where="post")
    plt.legend()
    plt.grid(True)
    plt.xlabel("Time [s]")
    plt.show()

if __name__ == "__main__":
    main()
