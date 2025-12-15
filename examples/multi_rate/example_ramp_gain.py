import numpy as np
import matplotlib.pyplot as plt

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks.sources import Ramp
from pySimBlocks.blocks.operators import Gain


def main():

    # ------------------------------------------------------------
    # Simulation parameters
    # ------------------------------------------------------------
    dt = 0.01
    T = 2.0

    # ------------------------------------------------------------
    # Blocks (NO sample_time specified → inherited mono-rate)
    # ------------------------------------------------------------
    ramp = Ramp(
        name="ramp",
        slope=1.0,          # y(t) = t
        start_time=0.0,
        offset=0.0
    )

    gain = Gain(
        name="gain",
        gain=2.0            # y = 2 * ramp
    )

    # ------------------------------------------------------------
    # Model
    # ------------------------------------------------------------
    model = Model("Ramp → Gain example")

    model.add_block(ramp)
    model.add_block(gain)

    model.connect("ramp", "out", "gain", "in")

    # ------------------------------------------------------------
    # Simulator (fixed-step, mono-rate)
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
            "gain.outputs.out"
        ]
    )

    # ------------------------------------------------------------
    # Plot results
    # ------------------------------------------------------------
    t = np.array(logs["time"]).flatten()
    ramp_out = np.vstack(logs["ramp.outputs.out"])
    gain_out = np.vstack(logs["gain.outputs.out"])

    plt.figure()
    plt.plot(t, ramp_out, label="Ramp output")
    plt.plot(t, gain_out, label="Gain output")
    plt.xlabel("Time [s]")
    plt.ylabel("Signal")
    plt.title("Ramp → Gain (mono-rate, inherited dt)")
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    main()
