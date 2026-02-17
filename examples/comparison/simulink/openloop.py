import numpy as np
import matplotlib.pyplot as plt
from pySimBlocks import Model, Simulator, SimulationConfig
from pySimBlocks.blocks.sources import Step
from pySimBlocks.blocks.systems import LinearStateSpace
from pySimBlocks.blocks.operators import Gain, Sum, Delay


def manual_sim(A, B, C, T, dt):

    # Blocks
    ref = Step("u", start_time=1., value_before=0., value_after=1.)
    delay_x = Delay("x", num_delays=1, initial_output=np.zeros((A.shape[0], 1)))
    gain_A = Gain("A", A, multiplication="Matrix (K @ u)")
    gain_B = Gain("B", B, multiplication="Matrix (K @ u)")
    gain_C = Gain("C", C, multiplication="Matrix (K @ u)")
    sum_x = Sum("sum_x", "++")

    # model
    model = Model("manual_ss")
    for blk in [ref, delay_x, gain_A, gain_B, gain_C, sum_x]:
        model.add_block(blk)

    # connection
    model.connect("u", "out", "B", "in")               # u -> B
    model.connect("B", "out", "sum_x", "in1")          # B u -> sum
    model.connect("x", "out", "A", "in")               # x -> A
    model.connect("A", "out", "sum_x", "in2")          # A x -> sum
    model.connect("sum_x", "out", "x", "in")           # x_next -> Delay
    model.connect("x", "out", "C", "in")               # x -> C

    # Simulator
    sim_cfg = SimulationConfig(dt, T, logging=[
                "u.outputs.out",
                "C.outputs.out",
                "x.outputs.out"
            ])
    sim = Simulator(model, sim_cfg, verbose=True)
    logs = sim.run( )
    
    time = sim.get_data("time")
    u = sim.get_data("u.outputs.out").squeeze()
    w = sim.get_data("C.outputs.out").squeeze()

    return time, u, w



def block_sim(A, B, C, T, dt):
    # Blocks
    ref = Step("command", start_time=1., value_before=0., value_after=1.)
    motor = LinearStateSpace("motor", A, B, C)

    # Model
    model = Model("DC Motor Control")
    for block in [ref, motor]:
        model.add_block(block)
    model.connect("command", "out", "motor", "u")

    # Simulator
    sim_cfg = SimulationConfig(dt, T, logging=[
                "command.outputs.out",
                "motor.outputs.y"
            ])
    sim = Simulator(model, sim_cfg, verbose=False)
    logs = sim.run()

    time = sim.get_data("time")
    u = sim.get_data("command.outputs.out").squeeze()
    w = sim.get_data("motor.outputs.y").squeeze()

    return time, u, w


def main():
    # DC Motor parameters
    R = 0.1
    L = 0.5
    J = 0.01
    K = 0.1
    a = 0.001

    # Simulation parameters
    dt = 0.1
    T = 30.

    # State-space matrices
    A = np.array([[1-dt*R/L, -dt*K/L], [dt*K/J, 1-dt*a/J]])
    B = np.array([[dt/L], [0]])
    C = np.array([[0, 1]])

    time, uol, wol = manual_sim(A, B, C, T, dt)
    time_block, uol_block, wol_block = block_sim(A, B, C, T, dt)

    # data from simulink
    data = np.load("simulation.npz")
    t_sim = data["time"]
    uol_sim, wol_sim = data["uol"], data["wol"]

    print("Error simulink - manual: ", np.linalg.norm(wol_sim - wol))
    print("Error simulink - block: ", np.linalg.norm(wol_sim - wol_block))

    # Plot
    plt.figure()
    plt.step(t_sim, wol_sim, '-r', label="w ((simulink)", where="post")
    plt.step(time, wol, '--b', label="w (manual)", where="post")
    plt.step(time_block, wol_block, ':g', label="w (block)", where="post")
    plt.xlabel("Time (s)")
    plt.ylabel("Speed (rad/s)")
    plt.legend()
    plt.grid()
    plt.title("Open-Loop DC Motor Response")

    plt.figure()
    plt.step(t_sim, uol_sim, '-r', label="u (simulink)", where="post")
    plt.step(time, uol, '--b', label="u (Manual)", where="post")
    plt.step(time_block, uol_block, ':g', label="u (block)", where="post")
    plt.xlabel("Time (s)")
    plt.ylabel("motor (V)")
    plt.legend()
    plt.grid()
    plt.title("Command")

    plt.show()

if __name__ == "__main__":
    main()
