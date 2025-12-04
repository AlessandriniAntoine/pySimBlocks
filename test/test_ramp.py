import numpy as np

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks import Ramp


def main():
    # --------------------------------------
    # 1. Define slope parameters (1D)
    # --------------------------------------
    slope = np.array([[2.0]])          # slope = 2.0
    start_time = 0.5                    # slope starts at t = 0.5 s
    initial_output = np.array([[1.0]])  # value at t < 0.5 is 1.0

    # --------------------------------------
    # 2. Create block
    # --------------------------------------
    src = Ramp(
        name="slope",
        slope=slope,
        start_time=start_time,
        initial_output=initial_output,
    )

    # --------------------------------------
    # 3. Build model
    # --------------------------------------
    model = Model(name="slope_test")
    model.add_block(src)

    # --------------------------------------
    # 4. Simulator
    # --------------------------------------
    dt = 0.01
    sim = Simulator(model, dt=dt)

    # --------------------------------------
    # 5. Run simulation
    # --------------------------------------
    T = 3.0
    logs = sim.run(
        T=T,
        variables_to_log=[
            "slope.outputs.out",
        ],
    )

    # --------------------------------------
    # 6. Convert logs to arrays
    # --------------------------------------
    y_sim = np.array(logs["slope.outputs.out"]).reshape(-1, 1)

    t = np.arange(0, T, dt)
    N = min(len(t), len(y_sim))
    t = t[:N]
    y_sim = y_sim[:N]

    # --------------------------------------
    # 7. Compute analytic reference
    # --------------------------------------
    # y(t) = initial_output + slope * max(0, t - start_time)
    y_ref = initial_output + slope * np.maximum(0.0, t.reshape(-1, 1) - start_time)

    # --------------------------------------
    # 8. Compare error
    # --------------------------------------
    error = np.linalg.norm(y_ref - y_sim)
    assert error < 1e-10, "SlopeSource output does not match analytic reference!"


if __name__ == "__main__":
    main()
    print("test_ramp passed.")
