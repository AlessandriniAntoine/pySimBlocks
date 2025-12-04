import numpy as np

from pySimBlocks import Model, Simulator
from pySimBlocks.blocks import Sinusoidal
from pySimBlocks.blocks import DiscreteIntegrator


def test_integrator():
    dt = 0.01
    T = 2.0

    # Input: a * sin(2pi f t)
    src = Sinusoidal("ref",
                            amplitude=1.0,
                            frequency=1.5,
                            phase=0.0,
                            offset=0.0)

    integ = DiscreteIntegrator("int", initial_state=np.array([[0.]]))

    model = Model("int_test")
    model.add_block(src)
    model.add_block(integ)
    model.connect("ref", "out", "int", "in")

    sim = Simulator(model, dt=dt)

    logs = sim.run(T=T, variables_to_log=["int.outputs.out", "ref.outputs.out"])

    length = len(logs["ref.outputs.out"])
    r = np.array(logs["ref.outputs.out"]).reshape(length, -1)
    y = np.array(logs["int.outputs.out"]).reshape(length, -1)
    t = np.arange(0, len(y))*dt

    # Analytic integral: (1/(2pi f)) * (1 - cos(2pi f t))
    ref = (1/(2*np.pi*1.5)) * (1 - np.cos(2*np.pi*1.5*t)).reshape(-1, 1)

    err = np.linalg.norm(y - ref)
    assert err < 1e-1 , f"Discrete Integrator test failed with error {err}"


if __name__ == "__main__":
    test_integrator()
    print("test_integrator passed.")
