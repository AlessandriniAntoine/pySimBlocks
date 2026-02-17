import numpy as np
import matplotlib.pyplot as plt
from pySimBlocks import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import LinearStateSpace
from pySimBlocks.blocks.operators import Sum, Gain, DiscreteIntegrator, DiscreteDerivator
from pySimBlocks.blocks.controllers import Pid


def manual_sim(A, B, C, Kp, Ki, Kd, T, dt):
    ref = Step("ref", start_time=1., value_before=0., value_after=1.)
    motor = LinearStateSpace("motor", A, B, C)
    error = Sum("error", "+-")
    kp = Gain("Kp", Kp, multiplication="Matrix (K @ u)")
    ki = Gain("Ki", Ki, multiplication="Matrix (K @ u)")
    integrator = DiscreteIntegrator("integrator", method="euler backward")
    kd = Gain("Kd", Kd, multiplication="Matrix (K @ u)")
    derivator = DiscreteDerivator("derivator")
    sum = Sum("sum", "+++")

    blocks = [ref, error, kp, integrator, ki, sum, motor, kd, derivator]

    model = Model("DC Motor Control")
    for block in blocks:
        model.add_block(block)
    model.connect("ref", "out", "error", "in1")
    model.connect("motor", "y", "error", "in2")
    model.connect("error", "out", "Kp", "in")
    model.connect("error", "out", "Ki", "in")
    model.connect("error", "out", "Kd", "in")
    model.connect("Kp", "out", "sum", "in1")
    model.connect("Ki", "out", "integrator", "in")
    model.connect("integrator", "out", "sum", "in3")
    model.connect("Kd", "out", "derivator", "in")
    model.connect("derivator", "out", "sum", "in2")
    model.connect("sum", "out", "motor", "u")

    # Simulator
    sim_cfg = SimulationConfig(dt, T, logging=[
                "ref.outputs.out",
                    "motor.outputs.y",
                    "sum.outputs.out",
                    "derivator.outputs.out",
                    "integrator.outputs.out",
                    "Kp.outputs.out"
                ])
    sim = Simulator(model, sim_cfg, verbose=False)
    logs = sim.run()

    time = sim.get_data("time")
    u = sim.get_data("sum.outputs.out").squeeze()
    w = sim.get_data("motor.outputs.y").squeeze()
    r = sim.get_data("ref.outputs.out").squeeze()

    return time, u, w, r

def block_sim(A, B, C, Kp, Ki, Kd, T, dt):
    ref = Step("ref", start_time=1., value_before=0., value_after=1.)
    motor = LinearStateSpace("motor", A, B, C)
    error = Sum("error", "+-")
    pid = Pid("pid", Kp=Kp, Ki=Ki, Kd=Kd, integration_method="euler backward")

    blocks = [ref, error, pid, motor]

    # Model
    model = Model("DC Motor Control")
    for block in blocks:
        model.add_block(block)
    model.connect("ref", "out", "error", "in1")
    model.connect("motor", "y", "error", "in2")
    model.connect("error", "out", "pid", "e")
    model.connect("pid", "u", "motor", "u")

    # Simulator
    sim_cfg = SimulationConfig(dt, T, logging=[
                "ref.outputs.out",
                "motor.outputs.y",
                "pid.outputs.u"
            ])
    sim = Simulator(model, sim_cfg, verbose=False)
    logs = sim.run()

    time = sim.get_data("time")
    u = sim.get_data("pid.outputs.u").squeeze()
    w = sim.get_data("motor.outputs.y").squeeze()
    r = sim.get_data("ref.outputs.out").squeeze()

    return time, u, w, r

def main():
    # DC Motor parameters
    R = 0.1
    L = 0.5
    J = 0.01
    K = 0.1
    a = 0.001

    Kp = np.array([[.001]])
    Ki = np.array([[.02]])
    Kd = np.array([[.01]])

    # Simulation parameters
    dt = 0.1
    T = 30.

    # State-space matrices
    A = np.array([[1-dt*R/L, -dt*K/L], [dt*K/J, 1-dt*a/J]])
    B = np.array([[dt/L], [0]])
    C = np.array([[0, 1]])

    time, upid, wpid, rpid = manual_sim(A, B, C, Kp, Ki, Kd, T, dt)
    time_block, upid_block, wpid_block, rpid_block = block_sim(A, B, C, Kp, Ki, Kd, T, dt)

    # data from simulink
    data = np.load("simulation.npz")
    t_sim = data["time"]
    upid_sim, wpid_sim, rpid_sim = data["upid_backward"], data["wpid_backward"], data['r']

    print("Error simulink - manual: ", np.linalg.norm(wpid_sim - wpid))
    print("Error simulink - block: ", np.linalg.norm(wpid_sim - wpid_block))

    # Plot
    plt.figure()
    plt.step(t_sim, wpid_sim, '-r', label="w (simulink)", where="post")
    plt.step(time, wpid, '--b', label="w (manual)", where="post")
    plt.step(time_block, wpid_block, ':g', label="w (block)", where="post")
    plt.xlabel("Time (s)")
    plt.ylabel("Speed (rad/s)")
    plt.legend()
    plt.grid()
    plt.title("PI DC Motor Response")

    plt.figure()
    plt.step(t_sim, upid_sim, '-r', label="u (simulink)", where="post")
    plt.step(time, upid, '--b', label="u (Manual)", where="post")
    plt.step(time_block, upid_block, ':g', label="u (block)", where="post")
    plt.xlabel("Time (s)")
    plt.ylabel("motor (V)")
    plt.legend()
    plt.grid()
    plt.title("Command")

    plt.figure()
    plt.step(t_sim, rpid_sim, '-r', label="r (simulink)", where="post")
    plt.step(time, rpid, '--b', label="r (Manual)", where="post")
    plt.step(time_block, rpid_block, ':g', label="r (block)", where="post")
    plt.xlabel("Time (s)")
    plt.legend()
    plt.grid()
    plt.title("Reference")

    plt.show()

if __name__ == "__main__":
    main()
