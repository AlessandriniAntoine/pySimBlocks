import matplotlib.pyplot as plt
import numpy as np

from pySimBlocks import Model, SimulationConfig, Simulator
from pySimBlocks.blocks.controllers import Pid
from pySimBlocks.blocks.operators import Sum
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import LinearStateSpace


def main():
    """This example demonstrates how to use the pySimBlocks library to create a 
    simple closed-loop control system with a step reference input, a PI controller, 
    and a linear state-space system.
    """

    A = np.array([[0.9]])
    B = np.array([[0.5]])
    C = np.array([[1.0]])
    x0 = np.zeros((A.shape[0], 1))

    Kp = np.array([[0.5]])
    Ki = np.array([[2.]])

    # -------------------------------------------------------
    # 1. Create the blocks
    # -------------------------------------------------------
    step = Step(
        name="ref",
        value_before=np.array([[0.0]]),
        value_after=np.array([[1.0]]),
        start_time=0.5
    )
    sum = Sum(name="error", signs="+-")
    pid = Pid(name="PID", controller="PI", Kp=Kp, Ki=Ki)
    system = LinearStateSpace(name="system", A=A, B=B, C=C, x0=x0)

    # -------------------------------------------------------
    # 2. Build the model
    # -------------------------------------------------------
    model = Model("test")
    for block in [step, sum, pid, system]:
        model.add_block(block)

    model.connect("ref", "out", "error", "in1")
    model.connect("system", "y", "error", "in2")
    model.connect("error", "out", "pid", "e")
    model.connect("pid", "u", "system", "u")

    # -------------------------------------------------------
    # 3. Create the simulator
    # -------------------------------------------------------
    dt = 0.01 # seconds
    T = 5. # seconds
    sim_cfg = SimulationConfig(dt, T)
    sim = Simulator(model, sim_cfg, verbose=False)

    # -------------------------------------------------------
    # 4. Run the simulation with logging
    # -------------------------------------------------------
    logs = sim.run(logging=[
            "ref.outputs.out",
            "pid.outputs.u",
            "system.outputs.y"
        ]
    )

    # -------------------------------------------------------
    # 5. Extract logged data
    # -------------------------------------------------------
    t = sim.get_data("time")
    u = sim.get_data("pid.outputs.u").squeeze()
    r = sim.get_data("ref.outputs.out").squeeze()
    y = sim.get_data("system.outputs.y").squeeze()

    # -------------------------------------------------------
    # 6. Plot the result
    # -------------------------------------------------------
    fig, axs = plt.subplots(1, 2, sharex=True)
    axs[0].step(t, r, "--r", label="ref", where="post")
    axs[0].step(t, y, "--b", label="output", where="post")
    axs[0].set_xlabel("Time [s]")
    axs[0].set_ylabel("Amplitude")
    axs[0].set_title("Closed-loop response")
    axs[0].grid(True)
    axs[0].legend()

    axs[1].step(t, u, "--b", label="u[k] (pid output)", where="post")
    axs[1].set_xlabel("Time [s]")
    axs[1].set_ylabel("Amplitude")
    axs[1].set_title("PID controller output")
    axs[1].grid(True)
    axs[1].legend()

    plt.show()


if __name__ == "__main__":
    main()
