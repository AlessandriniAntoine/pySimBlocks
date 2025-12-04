import numpy as np

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks import Step, Gain, Sum, Delay, LinearStateSpace


def main():
    """Closed chain block digram test.
    x[k+1] = A*x[k] + B*u[k]
    """
    A = np.array([[0.95, 0.1], [0, 0.98]])
    B = np.array([[1], [1]])
    x0 = np.array([[0.], [0.]])

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
    delay = Delay(name="delay", initial_output=x0)

    plant = LinearStateSpace(
        name="plant",
        A=A, B=B, C=np.eye(2),
        x0=x0,
    )

    # -------------------------------------------------------
    # 2. Build the model
    # -------------------------------------------------------
    model = Model("test")
    for block in [step, input_matrix, state_matrix, sum, delay, plant]:
        model.add_block(block)

    model.connect("u", "out", "B", "in")
    model.connect("B", "out", "sum", "in1")
    model.connect("A", "out", "sum", "in2")
    model.connect("sum", "out", "delay", "in")
    model.connect("delay", "out", "A", "in")
    model.connect("u", "out", "plant", "u")

    # -------------------------------------------------------
    # 3. Create the simulator
    # -------------------------------------------------------
    dt = 0.1
    sim = Simulator(model, dt=dt)

    # -------------------------------------------------------
    # 4. Run the simulation for 2 seconds
    # -------------------------------------------------------
    logs = sim.run(
        T=20.0,
        variables_to_log=[
            "u.outputs.out",
            "delay.outputs.out",
            "plant.outputs.x"
        ]
    )

    # -------------------------------------------------------
    # 5. Extract logged data
    # -------------------------------------------------------
    length = len(logs["plant.outputs.x"])
    u = np.array(logs["u.outputs.out"]).reshape(length, -1)
    x_delay = np.array(logs["delay.outputs.out"]).reshape(length, -1)
    x_plant = np.array(logs["plant.outputs.x"]).reshape(length, -1)
    t = np.arange(0, u.shape[0]) * dt

    error = np.linalg.norm(x_delay - x_plant)
    assert error < 1e-10, f"State error norm too high: {error}"



if __name__ == "__main__":
    main()
    print("test_delay_vs_statespace passed.")
