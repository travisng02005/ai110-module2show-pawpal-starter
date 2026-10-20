from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Optional


@dataclass
class Task:
    title: str
    category: str = "general"
    duration_minutes: int = 15
    priority: int = 2
    due_time: Optional[time] = None
    frequency: str = "once"
    completed: bool = False

    def mark_complete(self) -> Optional["Task"]:
        """Mark done; return the next occurrence if the task recurs."""
        pass

    def reschedule(self, new_time: time) -> None:
        pass

    def is_overdue(self, now: datetime) -> bool:
        pass

    def __str__(self) -> str:
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int = 0
    special_needs: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task: Task) -> None:
        pass

    def get_pending_tasks(self) -> list[Task]:
        pass

    def get_tasks_by_category(self, category: str) -> list[Task]:
        pass


@dataclass
class Owner:
    name: str
    available_minutes_per_day: int = 120
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet: Pet) -> None:
        pass

    def get_all_tasks(self) -> list[Task]:
        pass

    def get_available_time(self, on_date: date) -> int:
        pass


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.schedule: list[tuple[time, Task]] = []
        self.skipped_tasks: list[Task] = []

    def generate_schedule(self, on_date: date) -> list[tuple[time, Task]]:
        pass

    def detect_conflicts(self) -> list[tuple[Task, Task]]:
        pass

    def sort_by_time(self) -> list[tuple[time, Task]]:
        pass

    def sort_by_priority(self) -> list[tuple[time, Task]]:
        pass

    def filter_tasks(
        self, pet: Optional[Pet] = None, status: Optional[bool] = None
    ) -> list[Task]:
        pass

    def explain_plan(self) -> str:
        pass

    def get_next_task(self, now: datetime) -> Optional[Task]:
        pass
