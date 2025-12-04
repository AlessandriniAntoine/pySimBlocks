def generate_run(sim, plots):
    lines = []
    lines.append("from model import sim, T, dt")
    lines.append("import numpy as np")
    lines.append("import matplotlib.pyplot as plt\n")

    # HANDLE LOGGING SAFELY
    log_list = sim.get("log", [])   # <-- safe fallback

    lines.append("logs = sim.run(T=T, variables_to_log=[")

    for v in log_list:
        lines.append(f"    '{v}',")

    lines.append("])")
    lines.append("print('Simulation complete.')\n")

    # time
    lines.append("length = len(next(iter(logs.values())))")
    lines.append("time = np.arange(0, T, dt)[:length]\n")

    # Plot sections
    for fig in plots:
        title = fig["title"]
        vars_ = fig["log"]

        lines.append("plt.figure()")

        for var in vars_:
            safe_name = var.replace('.', '_').replace('[', '').replace(']', '')
            lines.append(f"{safe_name} = np.array(logs['{var}']).reshape(length, -1)")
            lines.append(f"for i in range({safe_name}.shape[1]):")
            lines.append(f"    plt.step(time, {safe_name}[:, i], where='post', label='{safe_name}'+str(i))")

        lines.append("plt.xlabel('Time [s]')")
        lines.append("plt.ylabel('Values')")
        lines.append(f"plt.title('{title}')")
        lines.append("plt.legend()")
        lines.append("plt.grid()\n")

    lines.append("plt.show()")

    return lines
