import numpy as np
import matplotlib.pyplot as plt
from pySimBlocks.project.build_parameters import build_parameters
from pySimBlocks.core.model import Model
from pySimBlocks.core.simulator import Simulator

sim_cfg, model_cfg = build_parameters("parameters.yaml")

model = Model(
    name="closed_loop",
    model_yaml="model.yaml",
    model_cfg=model_cfg
)

sim = Simulator(model, sim_cfg)

logs = sim.run()

length = len(logs["ref.outputs.out"])
t = np.array(logs["time"])
r = np.array(logs["ref.outputs.out"]).reshape(length, -1)
y = np.array(logs["plant.outputs.y"]).reshape(length, -1)
u = np.array(logs["pid.outputs.u"]).reshape(length, -1)

# -------------------------------------------------------
# 6. Plot the result
# -------------------------------------------------------
plt.figure()
plt.step(t, r, "--r", label="r[k] (step)", where="post")
plt.step(t, y, "--b", label="y[k] (plant)", where="post")
plt.xlabel("Time [s]")
plt.grid(True)
plt.legend()

plt.figure()
plt.step(t, u, "--b", label="u[k] (step)", where="post")
plt.xlabel("Time [s]")
plt.grid(True)
plt.legend()

plt.show()
