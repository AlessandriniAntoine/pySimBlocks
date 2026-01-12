import os
import numpy as np
import matplotlib.pyplot as plt

from pySimBlocks import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.operators import Sum
from pySimBlocks.blocks.controllers import Pid
from pySimBlocks.blocks.systems.sofa import SofaPlant


def main():

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Finger.py')

    # --- Create Blocks ---
    step = Step(
        name="step",
        value_before=[[0.0]],
        value_after=[[8.0]],
        start_time=0.4,
    )

    error = Sum(name="error", signs="+-")
    pid = Pid("pid", Kp=0.3, Ki=0.8, controller="PI")

    sofa_block = SofaPlant(
        name="sofa_finger",
        scene_file=path,
        input_keys=["cable"],
        output_keys=["measure"],
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
    T = 5.0
    sim_cfg = SimulationConfig(dt, T)
    sim = Simulator(model, sim_cfg)

    # --- Run simulation ---
    logs = sim.run(logging=[
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

    # gui data
    data_gui = np.load("data_gui.npz")
    t_gui = data_gui["time"]
    r_gui = data_gui["reference"]
    y_gui = data_gui["measure"]
    u_gui = data_gui["command"]

    print(f"t error: {np.linalg.norm(t - t_gui)}")
    print(f"r error: {np.linalg.norm(r - r_gui)}")
    print(f"y error: {np.linalg.norm(y - y_gui)}")
    print(f"u error: {np.linalg.norm(u - u_gui)}")

    plt.figure()
    plt.step(t, r, '--r', label="r (Inline)")
    plt.step(t, y[:, 0], '--b', label=f"y (Inline)")
    plt.step(t_gui, r_gui, ':m', label="r (GUI)")
    plt.step(t_gui, y_gui[:, 0], ':g', label=f"y (GUI)")
    plt.legend()
    plt.grid(True)
    plt.xlabel("Time [s]")
    plt.ylabel("Tip Position")
    plt.title("Finger Tip Position Over Time")

    plt.figure()
    plt.step(t, u[:, 0], '--b', label="u (Inline)")
    plt.step(t_gui, u_gui[:, 0], ':g', label="u (Gui)")
    plt.legend()
    plt.grid(True)
    plt.xlabel("Time [s]")
    plt.ylabel("Control Signal")
    plt.title("Control Signal Over Time")
    plt.show()


if __name__ == '__main__':
    main()
