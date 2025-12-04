import numpy as np
import control as ct

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks import Step, LinearStateSpace


def main():
    # --- 1. Define system matrices (SISO example) ---
    A = np.array([[0.7, 0.1], [0, 0.6]])
    B = np.array([[1], [1]])
    C = np.array([[1., 0.]])
    x0 = np.array([[0.], [0.]])

    # --- 2. Create blocks ---
    ref = Step(
        name="ref",
        value_before=np.array([[0.0]]),
        value_after=np.array([[1.0]]),
        t_step=0.2,
    )

    # Linear state-space system
    plant = LinearStateSpace(
        name="plant",
        A=A, B=B, C=C,
        x0=x0,
    )

    # --- 3. Build the model ---
    model = Model(name="linear_state_space_plant")
    model.add_block(ref)
    model.add_block(plant)

    # Connect:
    model.connect("ref", "out", "plant", "u")

    # --- 4. Create the simulator ---
    dt = 0.1  # 10 ms
    sim = Simulator(model, dt=dt)

    # --- 5. Run simulation ---
    T = 2.2  # 2 seconds
    logs = sim.run(
        T=T,
        variables_to_log=[
            "ref.outputs.out",
            "plant.outputs.x",
            "plant.outputs.y"
        ],
    )


    # --- 6. Inspect / print some results ---
    t = np.arange(0, T+dt, dt)
    length = min(len(t), len(logs["plant.outputs.x"]))
    t = t[:length]

    u = np.array(logs["ref.outputs.out"]).reshape(length, -1)
    x_plant = np.array(logs["plant.outputs.x"]).reshape(length, -1)
    y_plant = np.array(logs["plant.outputs.y"]).reshape(length, -1)


    # Compute true linear state - space
    sys = ct.ss(A, B, C, 0, dt=dt)
    _, yout, xout = ct.forced_response(sys, T=t, inputs=u.T, initial_state=x0.flatten(), return_states=True)
    x_true = xout.T
    y_true = yout.reshape(length, -1)

    state_error = np.linalg.norm(x_true - x_plant)
    assert state_error < 1e-10, f"State error norm too high: {state_error}"

    output_error = np.linalg.norm(y_true - y_plant)
    assert output_error < 1e-10, f"Output error norm too high: {output_error}"


if __name__ == "__main__":
    main()
    print("test_linear_state_space passed.")
