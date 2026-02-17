import numpy as np
import matplotlib.pyplot as plt
from pySimBlocks import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import LinearStateSpace
from pySimBlocks.blocks.operators import Sum, Gain, DiscreteIntegrator
from pySimBlocks.blocks.controllers import Pid


def manual_sim(A, B, C, Kp, Ki, T, dt):
    ref = Step("ref", start_time=1., value_before=0., value_after=1.)
    motor = LinearStateSpace("motor", A, B, C)
    error = Sum("error", "+-")
    kp = Gain("Kp", Kp, multiplication="Matrix (K @ u)")
    ki = Gain("Ki", Ki, multiplication="Matrix (K @ u)")
    integrator = DiscreteIntegrator("integrator")
    sum = Sum("sum", "++")

    blocks = [ref, error, kp, integrator, ki, sum, motor]

    model = Model("DC Motor Control")
    for block in blocks:
        model.add_block(block)
    model.connect("ref", "out", "error", "in1")
    model.connect("motor", "y", "error", "in2")
    model.connect("error", "out", "Kp", "in")
    model.connect("Kp", "out", "sum", "in1")
    model.connect("error", "out", "Ki", "in")
    model.connect("Ki", "out", "integrator", "in")
    model.connect("integrator", "out", "sum", "in2")
    model.connect("sum", "out", "motor", "u")

    # Simulator
    sim_cfg = SimulationConfig(dt, T, logging=[
        "ref.outputs.out",
        "motor.outputs.y",
        "sum.outputs.out"])
    sim = Simulator(model, sim_cfg, verbose=True)
    logs = sim.run()

    time = sim.get_data("time")
    u = sim.get_data("sum.outputs.out").squeeze()
    w = sim.get_data("motor.outputs.y").squeeze()
    r = sim.get_data("ref.outputs.out").squeeze()

    return time, u, w, r


def block_sim(A, B, C, Kp, Ki, T, dt):
    ref = Step("ref", start_time=1., value_before=0., value_after=1.)
    motor = LinearStateSpace("motor", A, B, C)
    error = Sum("error", "+-")
    pid = Pid("pid", Kp=Kp, Ki=Ki, controller="PI")

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
    sim = Simulator(model, sim_cfg, verbose=True)
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

    # Simulation parameters
    data = np.load("simulation.npz")
    dt = 0.1
    T = 30.

    # State-space matrices
    A = np.array([[1-dt*R/L, -dt*K/L], [dt*K/J, 1-dt*a/J]])
    B = np.array([[dt/L], [0]])
    C = np.array([[0, 1]])

    time, upi, wpi, rpi = manual_sim(A, B, C, Kp, Ki, T, dt)
    time_block, upi_block, wpi_block, rpi_block = block_sim(A, B, C, Kp, Ki, T, dt)

    # data from simulink
    t_sim = data["time"]
    upi_sim, wpi_sim, rpi_sim = data["upi"], data["wpi"], data['r']


    print("Error simulink - manual: ", np.linalg.norm(wpi_sim - wpi))
    print("Error simulink - block: ", np.linalg.norm(wpi_sim - wpi_block))

    # Plot
    plt.figure()
    plt.step(t_sim, wpi_sim, '-r', label="w (simulink)", where="post")
    plt.step(time, wpi, '--b', label="w (manual)", where="post")
    plt.step(time_block, wpi_block, ':g', label="w (block)", where="post")
    plt.xlabel("Time (s)")
    plt.ylabel("Speed (rad/s)")
    plt.legend()
    plt.grid()
    plt.title("PI DC Motor Response")

    plt.figure()
    plt.step(t_sim, upi_sim, '-r', label="u (simulink)", where="post")
    plt.step(time, upi, '--b', label="u (Manual)", where="post")
    plt.step(time_block, upi_block, ':g', label="u (block)", where="post")
    plt.xlabel("Time (s)")
    plt.ylabel("motor (V)")
    plt.legend()
    plt.grid()
    plt.title("Command")

    plt.figure()
    plt.step(t_sim, rpi_sim, '-r', label="r (simulink)", where="post")
    plt.step(time, rpi, '--b', label="r (Manual)", where="post")
    plt.step(time_block, rpi_block, ':g', label="r (block)", where="post")
    plt.xlabel("Time (s)")
    plt.legend()
    plt.grid()
    plt.title("Reference")

    plt.show()

if __name__ == "__main__":
    main()
