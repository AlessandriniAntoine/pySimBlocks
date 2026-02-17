import numpy as np
import matplotlib.pyplot as plt

from pySimBlocks import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.operators import Gain, Sum, Delay


def main():
    """Closed chain block digram test.
    x[k+1] = A*x[k] + B*u[k]
    """

    A = np.array([[0., 0.25], [0.3, 0.91]]) 
    B = np.array([[0.5], [0.3]])    
    C = np.array([[0., 1.0]])  
    x0 = np.zeros((A.shape[0], 1))

    # -------------------------------------------------------
    # 1. Create the blocks
    # -------------------------------------------------------
    step = Step(
        name="u",
        value_before=np.array([[0.0]]),
        value_after=np.array([[1.0]]),
        start_time=0.5
    )
    state_matrix = Gain(name="A", gain=A, multiplication="Matrix (K @ u)")
    input_matrix = Gain(name="B", gain=B, multiplication="Matrix (K @ u)")
    output_matrix = Gain(name="C", gain=C, multiplication="Matrix (K @ u)")
    sum = Sum(name="sum", signs="++")
    delay = Delay(name="delay", initial_output=x0)

    # -------------------------------------------------------
    # 2. Build the model
    # -------------------------------------------------------
    model = Model("test")
    for block in [step, input_matrix, state_matrix, sum, delay, output_matrix]:
        model.add_block(block)

    model.connect("u", "out", "B", "in")
    model.connect("B", "out", "sum", "in1")
    model.connect("A", "out", "sum", "in2")
    model.connect("sum", "out", "delay", "in")
    model.connect("delay", "out", "A", "in")
    model.connect("delay", "out", "C", "in")

    # -------------------------------------------------------
    # 3. Create the simulator
    # -------------------------------------------------------
    dt = 0.01
    T = 5.
    sim_cfg = SimulationConfig(dt, T)
    sim = Simulator(model, sim_cfg, verbose=True)

    # -------------------------------------------------------
    # 4. Run the simulation for 2 seconds
    # -------------------------------------------------------
    logs = sim.run(logging=[
            "u.outputs.out",
            "delay.outputs.out",
            "C.outputs.out",
        ]
    )

    # -------------------------------------------------------
    # 5. Extract logged data
    # -------------------------------------------------------
    t = sim.get_data("time")
    u = sim.get_data("u.outputs.out").squeeze()
    x = sim.get_data("delay.outputs.out").squeeze()
    y = sim.get_data("C.outputs.out").squeeze()

    # -------------------------------------------------------
    # 6. Plot the result
    # -------------------------------------------------------
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
