import numpy as np
import matplotlib.pyplot as plt

from pySimBlocks import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import LinearStateSpace

def main():
    # --- 1. Define system matrices (SISO example) ---
    A = np.array([[0., 0.25], [0.3, 0.91]]) 
    B = np.array([[0.5], [0.3]])    
    C = np.array([[0., 1.0]])     
    x0 = np.zeros((A.shape[0], 1))


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
        x0=x0,
    )

    # --- 3. Build the model ---
    model = Model(name="siso")
    model.add_block(command)
    model.add_block(plant)

    model.connect("command", "out", "plant", "u")


    # --- 4. Create the simulator ---
    dt = 0.01
    T = 5.
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
    t = sim.get_data("time")
    u = sim.get_data("command.outputs.out").squeeze()
    x = sim.get_data("plant.outputs.x").squeeze()
    y = sim.get_data("plant.outputs.y").squeeze()


    # --- 6. Plot the result ---
    plt.figure()
    plt.step(t, x[:, 0], "--r", label="x[0]", where="post")
    plt.step(t, x[:, 1], "--b", label="x[1]", where="post")
    plt.xlabel("Time [s]")
    plt.ylabel("State")
    plt.grid(True)
    plt.legend()
    plt.title("State evolution")

    plt.figure()
    plt.step(t, y, "--g", label="y (output)", where="post")
    plt.xlabel("Time [s]")
    plt.ylabel("Output")
    plt.grid(True)
    plt.legend()
    plt.title("Output evolution")

    plt.figure()
    plt.step(t, u, "--k", label="u (input)", where="post")
    plt.xlabel("Time [s]")
    plt.ylabel("Input")
    plt.grid(True)
    plt.legend()
    plt.title("Input signal")
    plt.show()

if __name__ == "__main__":
    main()
