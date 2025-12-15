class Scheduler:
    def __init__(self, tasks):
        self.tasks = sorted(tasks, key=lambda t: t.Ts)

    def active_tasks(self, t):
        return [task for task in self.tasks if task.should_run(t)]
