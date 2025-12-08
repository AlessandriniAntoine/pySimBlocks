import numpy as np
import matplotlib.pyplot as plt
from pySimBlocks import Model, Simulator
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import LinearStateSpace
from pySimBlocks.blocks.operators import Sum, Gain, DiscreteIntegrator


def manual(A, B, C, Kp, Ki, dt, T):
    ref = Step("ref", start_time=1., value_before=0., value_after=1.)
    motor = LinearStateSpace("motor", A, B, C)
    error = Sum("error", signs=[+1, -1])
    kp = Gain("Kp", Kp)
    ki = Gain("Ki", Ki)
    integrator = DiscreteIntegrator("integrator")
    sum = Sum("sum", num_inputs=2, signs=[+1, +1])

    blocks = [ref, error, kp, integrator, ki, sum, motor]

    model = Model("DC Motor Control")
    for block in blocks:
        model.add_block(block)
    model.connect("ref", "out", "error", "in1")
    model.connect("motor", "y", "error", "in2")
    model.connect("error", "out", "Kp", "in")
    model.connect("error", "out", "Ki", "in")
    model.connect("Kp", "out", "sum", "in1")
    model.connect("Ki", "out", "integrator", "in")
    model.connect("integrator", "out", "sum", "in2")
    model.connect("sum", "out", "motor", "u")

    # Simulator
    sim = Simulator(model, dt, verbose=False)

    logs = sim.run(T,
        variables_to_log=[
            "ref.outputs.out",
                "motor.outputs.y",
                "sum.outputs.out",
                "integrator.outputs.out",
                "Kp.outputs.out"
            ])

    length = len(logs["ref.outputs.out"])
    time = np.array(logs["time"])
    r = np.array(logs["ref.outputs.out"]).reshape(length, -1)
    w = np.array(logs["motor.outputs.y"]).reshape(length, -1)
    u = np.array(logs["sum.outputs.out"]).reshape(length, -1)

    print("PI:")
    print(w[-5:].flatten())

    p_term = np.array(logs["Kp.outputs.out"]).reshape(length, -1)
    i_term = np.array(logs["integrator.outputs.out"]).reshape(length, -1)


    return time, r, w, u, p_term, i_term

def main():
    # DC Motor parameters
    R = 0.1
    L = 0.5
    J = 0.01
    K = 0.1
    a = 0.001

    Kp = np.array([[0.001]])
    Ki = np.array([[0.02]])

    # Simulation parameters
    dt = 0.01
    T = 100.

    # State-space matrices
    A = np.array([[1-dt*R/L, -dt*K/L], [dt*K/J, 1-dt*a/J]])
    B = np.array([[dt/L], [0]])
    C = np.array([[0, 1]])


    time_man, r_man, w_man, u_man, p_term, i_term = manual(A, B, C, Kp, Ki, dt, T)


    plt.figure()
    plt.step(time_man, r_man, ':r', label="Reference (Manual)", where='post')
    plt.step(time_man, w_man, ':b', label="Motor Speed (Manual)", where='post')
    plt.step(time_man, u_man, ':g', label="Control Input (Manual)", where='post')
    plt.xlabel("Time (s)")
    plt.ylabel("Speed (rad/s)")
    plt.title("DC Motor PI Speed Response")
    plt.legend()
    plt.grid()

    plt.figure()
    plt.step(time_man, p_term, '-r', label="P Term", where='post')
    plt.step(time_man, i_term, '-g', label="I Term", where='post')
    plt.xlabel("Time (s)")
    plt.ylabel("Term Value")
    plt.title("PID Controller Terms (Manual Implementation)")
    plt.legend()
    plt.grid()

    plt.show()

if __name__ == "__main__":
    main()
