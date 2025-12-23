from pySimBlocks.core.task import Task

class Scheduler:
    """A simple scheduler for managing tasks based on their start times."""
    def __init__(self, tasks: list[Task]):
        self.tasks = sorted(tasks, key=lambda t: t.sample_time)

    def active_tasks(self, t):
        """Return the list of tasks that should run at time t."""
        return [task for task in self.tasks if task.should_run(t)]
