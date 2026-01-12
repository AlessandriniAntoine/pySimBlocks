import numpy as np
import matplotlib.pyplot as plt
from pySimBlocks import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import LinearStateSpace
from pySimBlocks.blocks.operators import Sum, Gain, DiscreteIntegrator, DiscreteDerivator
from pySimBlocks.blocks.controllers import Pid


def pid(A, B, C, Kp, Ki, Kd, dt, T):
    ref = Step("ref", start_time=1., value_before=0., value_after=1.)
    motor = LinearStateSpace("motor", A, B, C)
    error = Sum("error", signs="+-")
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
    sim_cfg = SimulationConfig(dt, T)
    sim = Simulator(model, sim_cfg, verbose=False)
    logs = sim.run(logging=[
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

def manual(A, B, C, Kp, Ki, Kd, dt, T):
    ref = Step("ref", start_time=1., value_before=0., value_after=1.)
    motor = LinearStateSpace("motor", A, B, C)
    error = Sum("error", signs="+-")
    kp = Gain("Kp", Kp)
    ki = Gain("Ki", Ki)
    integrator = DiscreteIntegrator("integrator")
    kd = Gain("Kd", Kd)
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
    sim_cfg = SimulationConfig(dt, T)
    sim = Simulator(model, sim_cfg, verbose=False)
    logs = sim.run(logging=[
            "ref.outputs.out",
            "motor.outputs.y",
            "sum.outputs.out",
            "derivator.outputs.out",
            "integrator.outputs.out",
            "Kp.outputs.out"
            ])

    length = len(logs["ref.outputs.out"])
    time = np.array(logs["time"])
    r = np.array(logs["ref.outputs.out"]).reshape(length, -1)
    w = np.array(logs["motor.outputs.y"]).reshape(length, -1)
    u = np.array(logs["sum.outputs.out"]).reshape(length, -1)

    return time, r, w, u

def main():
    # DC Motor parameters
    R = 0.1
    L = 0.5
    J = 0.01
    K = 0.1
    a = 0.001

    Kp = np.array([[0.001]])
    Ki = np.array([[0.02]])
    Kd = np.array([[0.01]])

    # Simulation parameters
    dt = 0.01
    T = 30.

    # State-space matrices
    A = np.array([[1-dt*R/L, -dt*K/L], [dt*K/J, 1-dt*a/J]])
    B = np.array([[dt/L], [0]])
    C = np.array([[0, 1]])


    time_pid, r_pid, w_pid, u_pid = pid(A, B, C, Kp, Ki, Kd, dt, T)
    time_man, r_man, w_man, u_man = manual(A, B, C, Kp, Ki, Kd, dt, T)

    error = np.linalg.norm(w_pid - w_man)
    print(f"Error between PID block and manual implementation: {error:.6f}")
    print("Mean Error: ", np.mean(np.abs(w_pid - w_man)))

    print("Time: ", time_pid[98:105].flatten())
    print("PID w: ", w_pid[98:105].flatten())
    print("Man w: ", w_man[98:105].flatten())
    print("PID u: ", u_pid[98:105].flatten())
    print("Man u: ", u_man[98:105].flatten())

    plt.figure()
    plt.step(time_pid, r_pid, '--r', label="Reference (PID)", where='post')
    plt.step(time_pid, w_pid, '--b', label="Motor Speed (PID)", where='post')
    plt.step(time_man, r_man, ':r', label="Reference (Manual)", where='post')
    plt.step(time_man, w_man, ':b', label="Motor Speed (Manual)", where='post')
    plt.xlabel("Time (s)")
    plt.ylabel("Speed (rad/s)")
    plt.title("DC Motor Speed Response")
    plt.legend()
    plt.grid()


    plt.figure()
    plt.step(time_pid, u_pid, '--g', label="Control Input (PID)", where='post')
    plt.step(time_man, u_man, ':g', label="Control Input (Manual)", where='post')
    plt.show()

if __name__ == "__main__":
    main()
