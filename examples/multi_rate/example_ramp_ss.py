import numpy as np
import matplotlib.pyplot as plt

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks.sources import Ramp
from pySimBlocks.blocks.systems import LinearStateSpace


def main():

    # ------------------------------------------------------------
    # Simulation parameters
    # ------------------------------------------------------------
    dt = 0.01      # base rate of the simulator
    T = 0.3

    # ------------------------------------------------------------
    # Ramp source (inherited rate)
    # ------------------------------------------------------------
    ramp = Ramp(
        name="ramp",
        slope=1.0,       # u(t) = t
        start_time=0.0,
        offset=0.0,
        sample_time=3*dt
    )

    # ------------------------------------------------------------
    # Discrete stable 1D state-space system
    #   x[k+1] = a x[k] + b u[k]
    #   y[k]   = x[k]
    #
    # ------------------------------------------------------------

    a = np.array([[0.9]])     # stable (|a| < 1)
    b = np.array([[1.0]])
    c = np.array([[1.0]])
    x0 = np.array([[0.0]])

    system = LinearStateSpace(
        name="plant",
        A=a,
        B=b,
        C=c,
        x0=x0,
    )

    # ------------------------------------------------------------
    # Model
    # ------------------------------------------------------------
    model = Model("Ramp → StateSpace (multi-rate)")

    model.add_block(ramp)
    model.add_block(system)

    model.connect("ramp", "out", "plant", "u")

    # ------------------------------------------------------------
    # Simulator
    # ------------------------------------------------------------
    sim = Simulator(
        model=model,
        dt=dt,
        mode="fixed",
        verbose=True
    )

    # ------------------------------------------------------------
    # Run simulation
    # ------------------------------------------------------------
    logs = sim.run(
        T=T,
        variables_to_log=[
            "ramp.outputs.out",
            "plant.outputs.y"
        ]
    )

    # ------------------------------------------------------------
    # Plot results
    # ------------------------------------------------------------
    t = np.array(logs["time"]).flatten()
    ramp_out = np.vstack(logs["ramp.outputs.out"])
    plant_out = np.vstack(logs["plant.outputs.y"])

    print(t)
    print(ramp_out.flatten())
    print(plant_out.flatten())

    plt.figure()
    plt.step(t, ramp_out, label="Ramp input", where="post")
    plt.step(t, plant_out, label="State-space output", where="post")
    plt.xlabel("Time [s]")
    plt.ylabel("Signal")
    plt.title("Ramp → 1D Stable State-Space (multi-rate)")
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    main()
