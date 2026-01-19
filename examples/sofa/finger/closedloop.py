import os

from pySimBlocks import Model, Simulator, SimulationConfig, PlotConfig
from pySimBlocks.blocks.systems.sofa import SofaPlant
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.operators import Sum
from pySimBlocks.blocks.controllers import Pid
from pySimBlocks.project import plot_from_config


def main():

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Finger.py')

    # --- Create Blocks ---
    step = Step(name="step", value_before=[[0.0]], value_after=[[8.0]], start_time=2.)
    error = Sum(name="error", signs="+-")
    pid = Pid("pid", controller="PI", Kp=0.3, Ki=0.8)

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
    T = 5.0
    sim_cfg = SimulationConfig(dt, T)
    sim = Simulator(model, sim_cfg, verbose=False)

    # --- Run simulation ---
    logs = sim.run(logging=[
            "step.outputs.out",
            "sofa_finger.outputs.measure",
            "pid.outputs.u"
        ],
    )

    # --- Inspect / print some results ---
    plot_cfg = PlotConfig([
            {'title': 'Ref vs Output',
            'signals': ['step.outputs.out', 'sofa_finger.outputs.measure']},
            {'title': 'Command',
            'signals': ['pid.outputs.u']}
    ])
    plot_from_config(logs, plot_cfg)



if __name__ == '__main__':
    main()
