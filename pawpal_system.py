from dataclasses import dataclass, field

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    name: str
    duration: int       # minutes
    priority: str       # "high", "medium", "low"
    frequency: str      # "daily", "weekly", "as_needed"
    completed: bool = False

    def mark_complete(self):
        self.completed = True

    def reset(self):
        self.completed = False


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        self.tasks.append(task)

    def get_pending_tasks(self) -> list[Task]:
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    name: str
    available_time: int     # minutes per day
    preferences: str = ""
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet):
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Returns all tasks across every pet."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> list[Task]:
        """Returns only incomplete tasks across every pet."""
        return [task for pet in self.pets for task in pet.get_pending_tasks()]


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    def generate_plan(self) -> list[Task]:
        """
        Picks tasks in priority order until the owner's available time is filled.
        Returns the list of tasks that fit in the day.
        """
        pending = self.owner.get_all_pending_tasks()
        sorted_tasks = sorted(pending, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))

        plan = []
        time_remaining = self.owner.available_time
        for task in sorted_tasks:
            if task.duration <= time_remaining:
                plan.append(task)
                time_remaining -= task.duration

        return plan

    def get_summary(self) -> str:
        """Returns a human-readable summary of the generated plan."""
        plan = self.generate_plan()
        if not plan:
            return "No tasks fit within the available time."

        lines = [f"{self.owner.name}'s plan for today ({self.owner.available_time} min available):"]
        for task in plan:
            lines.append(f"  [{task.priority.upper()}] {task.name} — {task.duration} min ({task.frequency})")

        total = sum(t.duration for t in plan)
        lines.append(f"Total: {total} / {self.owner.available_time} min used")
        return "\n".join(lines)
