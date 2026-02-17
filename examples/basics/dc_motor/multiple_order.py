import numpy as np
import matplotlib.pyplot as plt

from pySimBlocks import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import LinearStateSpace
from pySimBlocks.blocks.operators import Gain, Sum, DiscreteIntegrator


def main():
    # DC Motor parameters
    R = 0.1
    L = 0.5
    J = 0.01
    K = 0.1
    a = 0.001

    Kp = 0.001
    Ki = 0.02

    # Simulation parameters
    dt = 0.01
    T = 100.

    # State-space matrices
    A = np.array([[1-dt*R/L, -dt*K/L], [dt*K/J, 1-dt*a/J]])
    B = np.array([[dt/L], [0]])
    C = np.array([[0, 1]])

    # Model
    test_order = [
        [0, 6, 2, 1, 3, 4, 5],
        [0, 3, 2, 1, 6, 4, 5],
        [0, 1, 2, 3, 4, 5, 6],
        [0, 1, 2, 6, 4, 5, 3],
        [3, 2, 0, 1, 6, 4, 5],
        [4, 2, 6, 0, 1, 3, 5]
    ]
    for order in test_order:
        ref = Step("ref", start_time=1., value_before=0., value_after=1.)
        motor = LinearStateSpace("motor", A, B, C)
        error = Sum("error", signs="+-")
        kp = Gain("Kp", Kp)
        ki = Gain("Ki", Ki)
        integrator = DiscreteIntegrator("integrator")
        sum = Sum("sum", signs="++")

        blocks = [ref, error, kp, integrator, ki, sum, motor]

        model = Model("DC Motor Control")
        for i in order:
            model.add_block(blocks[i])
        model.connect("ref", "out", "error", "in1")
        model.connect("motor", "y", "error", "in2")
        model.connect("error", "out", "Kp", "in")
        model.connect("error", "out", "Ki", "in")
        model.connect("Ki", "out", "integrator", "in")
        model.connect("integrator", "out", "sum", "in2")
        model.connect("Kp", "out", "sum", "in1")
        model.connect("sum", "out", "motor", "u")

        # Simulator
        sim_cfg = SimulationConfig(dt, T)
        sim = Simulator(model, sim_cfg, verbose=False)

        logs = sim.run(logging=[
                "ref.outputs.out",
                "motor.outputs.y",
                "sum.outputs.out"
            ])

        time = sim.get_data("time")
        r = sim.get_data("ref.outputs.out").squeeze()
        w = sim.get_data("motor.outputs.y").squeeze()
        u = sim.get_data("sum.outputs.out").squeeze()

        print(w[-5:].flatten())

        plt.figure()
        plt.step(time, r, '--r', label="Reference (rad/s)", where='post')
        plt.step(time, w, '--b', label="Motor Speed (rad/s)", where='post')
        plt.step(time, u, '--g', label="Control Input (V)", where='post')
        plt.xlabel("Time (s)")
        plt.ylabel("Speed (rad/s)")
        plt.title("DC Motor Speed Response")
        plt.legend()
        plt.grid()
        plt.show()

if __name__ == "__main__":
    main()
