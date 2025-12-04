import numpy as np
import matplotlib.pyplot as plt

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks import Step, Gain, Sum, Delay


def main():
    """Closed chain block digram test.
    x[k+1] = A*x[k] + B*u[k]
    """

    A = np.array([[0.9]])
    B = np.array([[1.0]])

    # -------------------------------------------------------
    # 1. Create the blocks
    # -------------------------------------------------------
    step = Step(
        name="u",
        value_before=np.array([[0.0]]),
        value_after=np.array([[1.0]]),
        t_step=0.5
    )
    state_matrix = Gain(name="A", gain=A)
    input_matrix = Gain(name="B", gain=B)
    sum = Sum(name="sum", num_inputs=2, signs=[1, 1])
    delay = Delay(name="delay", initial_output=np.zeros((1, 1)))

    # -------------------------------------------------------
    # 2. Build the model
    # -------------------------------------------------------
    model = Model("test")
    for block in [step, input_matrix, state_matrix, sum, delay]:
        model.add_block(block)

    model.connect("u", "out", "B", "in")
    model.connect("B", "out", "sum", "in1")
    model.connect("A", "out", "sum", "in2")
    model.connect("sum", "out", "delay", "in")
    model.connect("delay", "out", "A", "in")

    # -------------------------------------------------------
    # 3. Create the simulator
    # -------------------------------------------------------
    dt = 0.1
    sim = Simulator(model, dt=dt)

    # -------------------------------------------------------
    # 4. Run the simulation for 2 seconds
    # -------------------------------------------------------
    logs = sim.run(
        T=2.0,
        variables_to_log=[
            "u.outputs.out",
            "delay.outputs.out"
        ]
    )

    # -------------------------------------------------------
    # 5. Extract logged data
    # -------------------------------------------------------
    length = len(logs["u.outputs.out"])
    u = np.array(logs["u.outputs.out"]).reshape(length, -1)
    x = np.array(logs["delay.outputs.out"]).reshape(length, -1)
    t = np.arange(0, x.shape[0]) * dt

    print(f"Time: \n{t.flatten()}")
    print(f"u: \n{u.flatten()}")
    print(f"x: \n{x.flatten()}")

    # -------------------------------------------------------
    # 6. Plot the result
    # -------------------------------------------------------
    plt.figure()
    plt.plot(t, u, "--b", label="u[k] (step)")
    plt.plot(t, x, "--r", label="x[k] (delay)")
    plt.xlabel("Time [s]")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.legend()
    plt.title("Step Test")
    plt.show()


if __name__ == "__main__":
    main()
