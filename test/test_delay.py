import numpy as np

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks import Step, Delay

def run_delay_test(num_delays, dt, T, initial_output=None):
    """
    Utility function returning reference signal and delayed signal.
    """

    # Step: 0 -> 1 at t_step = 0.5
    ref = Step(
        name="ref",
        value_before=np.array([[0.0]]),
        value_after=np.array([[1.0]]),
        t_step=0.1
    )

    delay = Delay(
        name="delay",
        num_delays=num_delays,
        initial_output=initial_output
    )

    model = Model("delay_test")
    model.add_block(ref)
    model.add_block(delay)
    model.connect("ref", "out", "delay", "in")

    sim = Simulator(model, dt=dt)
    logs = sim.run(
        T=T,
        variables_to_log=["ref.outputs.out", "delay.outputs.out"]
    )

    length = len(logs["ref.outputs.out"])
    ref_log = np.array(logs["ref.outputs.out"]).reshape(length, -1)
    delay_log = np.array(logs["delay.outputs.out"]).reshape(length, -1)

    return ref_log, delay_log

def main():

    num_delays = 3
    dt = 0.1
    T = 2.0

    ref, delayed = run_delay_test(num_delays, dt, T, np.array([[0.0]]))

    ref_cut = ref[:-num_delays]
    delayed_cut = delayed[num_delays:]

    error = np.linalg.norm(ref_cut - delayed_cut)
    assert error < 1e-6, f"Delay block test failed with error {error}"



if __name__ == "__main__":
    main()
    print("test_delay passed.")
