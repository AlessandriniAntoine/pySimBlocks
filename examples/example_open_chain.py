import numpy as np
import matplotlib.pyplot as plt

from pySimBlocks import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.operators import Gain, Sum


def main():
    """Open chain block digram test.
    s = g * r1 + r2
    """

    # -------------------------------------------------------
    # 1. Create the blocks
    # -------------------------------------------------------
    step1 = Step(
        name="r1",
        value_before=np.array([[0.0]]),
        value_after=np.array([[1.0]]),
        start_time=0.5
    )
    step2 = Step(
        name="r2",
        value_before=np.array([[0.0]]),
        value_after=np.array([[1.0]]),
        start_time=0.5
    )
    gain = Gain(name="g", gain=2.0)
    sum = Sum(name="s", signs="++")

    # -------------------------------------------------------
    # 2. Build the model
    # -------------------------------------------------------
    model = Model("test")
    for block in [step1, step2, gain, sum]:
        model.add_block(block)

    model.connect("r1", "out", "g", "in")
    model.connect("g", "out", "s", "in1")
    model.connect("r2", "out", "s", "in2")

    # -------------------------------------------------------
    # 3. Create the simulator
    # -------------------------------------------------------
    dt = 0.1
    T = 2.0
    sim_cfg = SimulationConfig(dt, T)
    sim = Simulator(model, sim_cfg)

    # -------------------------------------------------------
    # 4. Run the simulation for 2 seconds
    # -------------------------------------------------------
    logs = sim.run(logging=[
            "r1.outputs.out",
            "r2.outputs.out",
            "g.outputs.out",
            "s.outputs.out"
        ]
    )

    # -------------------------------------------------------
    # 5. Extract logged data
    # -------------------------------------------------------
    length = len(logs["r1.outputs.out"])
    t = np.array(logs["time"])
    r1 = np.array(logs["r1.outputs.out"]).reshape(length, 1)
    r2 = np.array(logs["r2.outputs.out"]).reshape(length, 1)
    g = np.array(logs["g.outputs.out"]).reshape(length, 1)
    s = np.array(logs["s.outputs.out"]).reshape(length, 1)

    print(f"Time: \n{t.flatten()}")
    print(f"r1: \n{r1.flatten()}")
    print(f"r2: \n{r2.flatten()}")
    print(f"g: \n{g.flatten()}")
    print(f"s: \n{s.flatten()}")

    # -------------------------------------------------------
    # 6. Plot the result
    # -------------------------------------------------------
    plt.figure()
    plt.step(t, r1, "--b", label="r1[k] (step)", where="post")
    plt.step(t, r2, "--r", label="r2[k] (step)", where="post")
    plt.step(t, g, "--g", label="g[k] (gain)", where="post")
    plt.step(t, s, "--m", label="s[k] (sum)", where="post")
    plt.xlabel("Time [s]")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.legend()
    plt.title("Step Test")
    plt.show()


if __name__ == "__main__":
    main()
