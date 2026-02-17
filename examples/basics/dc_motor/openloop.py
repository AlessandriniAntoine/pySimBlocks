import numpy as np
import matplotlib.pyplot as plt
from pySimBlocks import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import LinearStateSpace


def main():
    # DC Motor parameters
    R = 0.1
    L = 0.5
    J = 0.01
    K = 0.1
    a = 0.001

    # Simulation parameters
    dt = 0.01
    T = 100.

    # State-space matrices
    A = np.array([[1-dt*R/L, -dt*K/L], [dt*K/J, 1-dt*a/J]])
    B = np.array([[dt/L], [0]])
    C = np.array([[0, 1]])

    # Blocks
    ref = Step("command", start_time=1., value_before=0., value_after=1.)
    motor = LinearStateSpace("motor", A, B, C)


    # Model
    model = Model("DC Motor Control")
    for block in [ref, motor]:
        model.add_block(block)
    model.connect("command", "out", "motor", "u")

    # Simulator
    sim_cfg = SimulationConfig(dt, T, logging=[
        "command.outputs.out",
        "motor.outputs.y"
    ])
    sim = Simulator(model, sim_cfg)
    logs = sim.run()

    time = sim.get_data("time")
    u = sim.get_data("command.outputs.out").squeeze()
    w = sim.get_data("motor.outputs.y").squeeze()

    print("Open-Loop DC Motor Response:")
    print(w[-5:].flatten())

    plt.figure()
    plt.step(time, w, '--b', label="Motor Speed (rad/s)")
    plt.step(time, u, '--g', label="Control Input (V)")
    plt.xlabel("Time (s)")
    plt.ylabel("Speed (rad/s)")
    plt.legend()
    plt.grid()
    plt.title("Open-Loop DC Motor Response")
    plt.show()

if __name__ == "__main__":
    main()
