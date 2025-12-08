import numpy as np
import matplotlib.pyplot as plt
from pySimBlocks import Model, Simulator
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import LinearStateSpace
from pySimBlocks.blocks.operators import Sum, Gain, DiscreteIntegrator, DiscreteDerivator
from pySimBlocks.blocks.controllers import Pid


def pid(A, B, C, Kp, Ki, Kd, dt, T):
    ref = Step("ref", start_time=1., value_before=0., value_after=1.)
    motor = LinearStateSpace("motor", A, B, C)
    error = Sum("error", signs=[+1, -1])
    pid = Pid("pid", Kp=Kp, Ki=Ki, Kd=Kd)

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
    sim = Simulator(model, dt, verbose=False)

    logs = sim.run(T,
        variables_to_log=[
            "ref.outputs.out",
            "motor.outputs.y",
            "pid.outputs.u"
        ])

    length = len(logs["ref.outputs.out"])
    time = np.array(logs["time"])
    r = np.array(logs["ref.outputs.out"]).reshape(length, -1)
    w = np.array(logs["motor.outputs.y"]).reshape(length, -1)
    u = np.array(logs["pid.outputs.u"]).reshape(length, -1)
    return time, r, w, u


def main():
    # DC Motor parameters
    R = 0.1
    L = 0.5
    J = 0.01
    K = 0.1
    a = 0.001

    Kp = 0.001
    Ki = 0.02
    Kd = 0.01

    # Simulation parameters
    dt = 0.01
    T = 100.

    # State-space matrices
    A = np.array([[1-dt*R/L, -dt*K/L], [dt*K/J, 1-dt*a/J]])
    B = np.array([[dt/L], [0]])
    C = np.array([[0, 1]])


    time_pid, r_pid, w_pid, u_pid = pid(A, B, C, Kp, Ki, Kd, dt, T)


    plt.figure()
    plt.step(time_pid, r_pid, '--r', label="Reference (PID)", where='post')
    plt.step(time_pid, w_pid, '--b', label="Motor Speed (PID)", where='post')
    plt.step(time_pid, u_pid, '--g', label="Control Input (PID)", where='post')
    plt.xlabel("Time (s)")
    plt.ylabel("Speed (rad/s)")
    plt.title("DC Motor Speed Response")
    plt.legend()
    plt.grid()
    plt.show()

if __name__ == "__main__":
    main()
