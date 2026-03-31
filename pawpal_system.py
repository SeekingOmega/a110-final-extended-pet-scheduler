from dataclasses import dataclass, field


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: str = ""


@dataclass
class Owner:
    name: str
    available_time: int  # minutes per day
    preferences: str = ""
    pets: list["Pet"] = field(default_factory=list)


@dataclass
class Task:
    name: str
    duration: int  # minutes
    priority: str  # "high", "medium", "low"


class Scheduler:
    def __init__(self, owner: Owner, tasks: list[Task]):
        self.owner = owner
        self.tasks = tasks

    def generate_plan(self) -> list[Task]:
        # TODO: sort tasks by priority and fit within owner.available_time
        pass
