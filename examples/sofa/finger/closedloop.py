import os
import numpy as np
import matplotlib.pyplot as plt

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks.systems import SofaPlant
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.operators import Sum
from pySimBlocks.blocks.controllers import Pid


def main():

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Finger.py')

    # --- Create Blocks ---
    step = Step(name="step", value_before=[[0.0]], value_after=[[8.0]], start_time=0.4)
    error = Sum(name="error", num_inputs=2, signs=[1, -1])
    pid = Pid("pid", Kp=0.3, Ki=0.8, Kd=0.000)

    sofa_block = SofaPlant(
        name="sofa_finger",
        scene_file=path,
        input_keys=["cable"],
        output_keys=["tip", "measure"],
    )

    # --- Build the model ---
    model = Model(name="sofa_finger_model")
    for block in [step, error, pid, sofa_block]:
        model.add_block(block)

    model.connect("step", "out", "error", "in1")
    model.connect("sofa_finger", "measure", "error", "in2")
    model.connect("error", "out", "pid", "e")
    model.connect("pid", "u", "sofa_finger", "cable")


    # --- Create the simulator ---
    dt = 0.01
    sim = Simulator(model, dt=dt, verbose=False)

    # --- Run simulation ---
    T = 5.0
    logs = sim.run(
        T=T,
        variables_to_log=[
            "step.outputs.out",
            "sofa_finger.outputs.measure",
            "pid.outputs.u"
        ],
    )

    # --- Inspect / print some results ---
    length = len(logs["step.outputs.out"])

    t = np.array(logs["time"])
    r = np.array(logs["step.outputs.out"]).reshape(length, -1)
    y = np.array(logs["sofa_finger.outputs.measure"]).reshape(length, -1)
    u = np.array(logs["pid.outputs.u"]).reshape(length, -1)

    plt.figure()
    plt.step(t, r, 'r--', label="Reference")
    plt.step(t, y[:, 0], 'b--', label=f"Measure")
    plt.legend()
    plt.grid(True)
    plt.xlabel("Time [s]")
    plt.ylabel("Tip Position")
    plt.title("Finger Tip Position Over Time")

    plt.figure()
    plt.step(t, u[:, 0], 'g--', label="Control Signal")
    plt.legend()
    plt.grid(True)
    plt.xlabel("Time [s]")
    plt.ylabel("Control Signal")
    plt.title("Control Signal Over Time")
    plt.show()


if __name__ == '__main__':
    main()
