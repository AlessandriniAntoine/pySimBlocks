from pySimBlocks import Model, Simulator, SimulationConfig, PlotConfig
from pySimBlocks.blocks.operators import Gain, Sum, DiscreteIntegrator
from pySimBlocks.project.plot_from_config import plot_from_config

# 1. Create the blocks
v = DiscreteIntegrator("v", initial_state=5)
x = DiscreteIntegrator("x", initial_state=2.)
damping = Gain(name="damping", gain=0.5)
stiffness = Gain(name="stiffness", gain=2)
sum = Sum(name="sum", signs="--")

# 2. Build the model
model = Model("Example")
for block in [v, x, damping, stiffness, sum]:
    model.add_block(block)

model.connect("v", "out", "x", "in")
model.connect("v", "out", "damping", "in")
model.connect("x", "out", "stiffness", "in")
model.connect("damping", "out", "sum", "in1")
model.connect("stiffness", "out", "sum", "in2")
model.connect("sum", "out", "v", "in")

# 3. Create the simulator
sim_cfg = SimulationConfig(dt=0.05, T=30.)
sim = Simulator(model, sim_cfg)

# 4. Run the simulation
logs = sim.run(logging=[
        "x.outputs.out",
        "v.outputs.out",
    ]
)

# 5. Plot the results
plot_cfg = PlotConfig([
    {"title": "Position and Velocity",
     "signals": ["x.outputs.out", "v.outputs.out"],},
    ])
plot_from_config(logs, plot_cfg)

