from multiprocessing import Process, Pipe
import numpy as np

def sofa_worker(conn):
    import Sofa
    from Finger import createScene

    root = Sofa.Core.Node("root")
    root, controller = createScene(root)
    Sofa.Simulation.initRoot(root)
    dt = root.dt.value
    Sofa.Simulation.animate(root, dt)  # Initial animate to setup

    outputs = {k: [] for k in controller.outputs}

    kp = 0.5
    integral = 0.0
    ki = 0.5

    for i in range(500):
        ref = 8.5 if i * dt > 0.4 else 0.0
        measure = controller.outputs["measure"].copy()
        outputs["tip"].append(controller.outputs["tip"].copy())
        outputs["measure"].append(measure.copy())
        controller.inputs["cable"] = kp * (ref - measure) + ki * integral
        integral += (ref - measure) * dt
        Sofa.Simulation.animate(root, dt)

    conn.send(outputs)
    conn.close()


def main():
    parent_conn, child_conn = Pipe()
    p = Process(target=sofa_worker, args=(child_conn,))
    p.start()
    outputs = parent_conn.recv()
    p.join()

    length = len(outputs["tip"])

    positions = np.array(outputs["tip"]).reshape(length, -3)
    measures = np.array(outputs["measure"]).reshape(length, -1)
    r = np.array([8.5 if t * 0.01 > 0.4 else 0.0 for t in range(length)])

    print("Simulation finished, position:", positions.shape)
    print("Simulation finished, measure:", measures.shape)

    # Plot without crash
    import matplotlib.pyplot as plt
    t = np.arange(len(positions)) * 0.01
    plt.step(t, positions[:, 1], label="Y")
    plt.step(t, r, 'k--', label="Reference Y")
    plt.legend()
    plt.show()


if __name__ == '__main__':
    main()
