from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Owner:
    name: str
    contact_info: str
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet: Pet) -> None:
        pass

    def get_pets(self) -> list[Pet]:
        pass


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    owner: Owner | None = None
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task: Task) -> None:
        pass

    def get_tasks(self) -> list[Task]:
        pass

    def get_tasks_due_on(self, target_date: date) -> list[Task]:
        pass


@dataclass
class Task:
    title: str
    category: str
    duration_minutes: int
    priority: str
    pet: Pet | None = None
    completed: bool = False
    recurrence: str | None = None
    last_completed_date: date | None = None
    next_due_date: date | None = None

    def mark_complete(self) -> None:
        pass

    def is_overdue(self, target_date: date) -> bool:
        pass

    def is_due(self, target_date: date) -> bool:
        pass


@dataclass
class DailyPlan:
    date: date
    pet: Pet
    time_budget_minutes: int
    scheduled_tasks: list[tuple] = field(default_factory=list)

    @classmethod
    def build(cls, pet: Pet, target_date: date, available_minutes: int) -> DailyPlan:
        pass

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        pass

    def filter_by_time(self, tasks: list[Task], budget: int) -> list[Task]:
        pass

    def detect_conflicts(self) -> list[tuple]:
        pass

    def total_duration(self) -> int:
        pass

    def remaining_time(self) -> int:
        pass

    def explain(self) -> str:
        pass
