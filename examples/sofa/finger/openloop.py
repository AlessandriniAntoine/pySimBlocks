import os

from pySimBlocks import Model, Simulator, SimulationConfig, PlotConfig
from pySimBlocks.blocks.systems.sofa import SofaPlant
from pySimBlocks.blocks.sources import Step
from pySimBlocks.project.plot_from_config import plot_from_config


def main():

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Finger.py')


    # --- Create Blocks ---
    step = Step(
        name="step",
        value_before=0.0,
        value_after=1.0,
        start_time=0.5,
    )

    sofa_block = SofaPlant(
        name="sofa_finger",
        scene_file=path,
        input_keys=["cable"],
        output_keys=["tip"],
    )

    # --- Build the model ---
    model = Model(name="sofa_finger_model")
    model.add_block(step)
    model.add_block(sofa_block)
    model.connect("step", "out", "sofa_finger", "cable")


    # --- Create the simulator ---
    dt = 0.01
    T = 5.0
    sim_cfg = SimulationConfig(dt, T)
    sim = Simulator(model, sim_cfg)

    # --- Run simulation ---
    logs = sim.run(logging=[
            "step.outputs.out",
            "sofa_finger.outputs.tip",
        ],
    )

    # --- Plotting ---
    plot_cfg = PlotConfig([
            {'title': 'Finger Tip Position',
            'signals': ['step.outputs.out', 'sofa_finger.outputs.tip']}
    ])
    plot_from_config(logs, plot_cfg)


if __name__ == '__main__':
    main()
