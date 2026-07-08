from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_RECURRENCE_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}


@dataclass(eq=False)
class Owner:
    name: str
    contact_info: str
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        """Attach a pet to this owner, avoiding duplicates."""
        pet.owner = self
        if pet not in self.pets:
            self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Detach a pet from this owner."""
        if pet in self.pets:
            self.pets.remove(pet)
        if pet.owner is self:
            pet.owner = None

    def get_pets(self) -> list[Pet]:
        """Return this owner's pets."""
        return self.pets

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks())
        return tasks


@dataclass(eq=False)
class Pet:
    name: str
    species: str
    breed: str
    age: int
    owner: Owner | None = None
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet, avoiding duplicates."""
        task.pet = self
        if task not in self.tasks:
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Detach a task from this pet."""
        if task in self.tasks:
            self.tasks.remove(task)
        if task.pet is self:
            task.pet = None

    def get_tasks(self) -> list[Task]:
        """Return this pet's tasks."""
        return self.tasks

    def get_tasks_due_on(self, target_date: date) -> list[Task]:
        """Return this pet's tasks due on or before the given date."""
        return [task for task in self.tasks if task.is_due(target_date)]


@dataclass(eq=False)
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

    def mark_complete(self, completed_date: date | None = None) -> None:
        """Mark this task complete and schedule its next occurrence if recurring."""
        completed_date = completed_date or self.next_due_date or date.today()
        self.completed = True
        self.last_completed_date = completed_date

        recurrence_days = _RECURRENCE_DAYS.get(self.recurrence)
        if recurrence_days is not None:
            self.next_due_date = completed_date + timedelta(days=recurrence_days)
            self.completed = False
        else:
            self.next_due_date = None

    def is_overdue(self, target_date: date) -> bool:
        """Return whether this task's due date has passed the given date."""
        if self.completed or self.next_due_date is None:
            return False
        return self.next_due_date < target_date

    def is_due(self, target_date: date) -> bool:
        """Return whether this task is due on or before the given date."""
        if self.completed or self.next_due_date is None:
            return False
        return self.next_due_date <= target_date


@dataclass
class Scheduler:
    date: date
    owner: Owner
    time_budget_minutes: int
    scheduled_tasks: list[tuple] = field(default_factory=list)

    @classmethod
    def build(cls, owner: Owner, target_date: date, available_minutes: int) -> Scheduler:
        """Build a scheduler with the owner's due tasks fitted to the time budget."""
        scheduler = cls(date=target_date, owner=owner, time_budget_minutes=available_minutes)

        due_pairs = [
            (pet, task)
            for pet in owner.get_pets()
            for task in pet.get_tasks_due_on(target_date)
        ]
        due_tasks = scheduler.sort_by_priority([task for _, task in due_pairs])
        fitted_tasks = scheduler.filter_by_time(due_tasks, available_minutes)

        pet_by_task = {task: pet for pet, task in due_pairs}
        scheduler.scheduled_tasks = [(pet_by_task[task], task) for task in fitted_tasks]
        return scheduler

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return the tasks sorted from highest to lowest priority."""
        return sorted(tasks, key=lambda task: _PRIORITY_ORDER.get(task.priority, len(_PRIORITY_ORDER)))

    def filter_by_time(self, tasks: list[Task], budget: int) -> list[Task]:
        """Return the tasks that fit within the given time budget."""
        fitted = []
        remaining = budget
        for task in tasks:
            if task.duration_minutes <= remaining:
                fitted.append(task)
                remaining -= task.duration_minutes
        return fitted

    def detect_conflicts(self) -> list[tuple]:
        """Return pairs of scheduled tasks that share the same pet and category."""
        conflicts = []
        seen: dict[tuple[Pet, str], Task] = {}
        for pet, task in self.scheduled_tasks:
            key = (pet, task.category)
            if key in seen:
                conflicts.append((seen[key], task))
            else:
                seen[key] = task
        return conflicts

    def total_duration(self) -> int:
        """Return the total duration in minutes of all scheduled tasks."""
        return sum(task.duration_minutes for _, task in self.scheduled_tasks)

    def remaining_time(self) -> int:
        """Return the unused minutes left in the time budget."""
        return self.time_budget_minutes - self.total_duration()

    def explain(self) -> str:
        """Return a human-readable summary of the schedule."""
        if not self.scheduled_tasks:
            return f"No tasks scheduled for {self.date}."

        lines = [f"Schedule for {self.date} ({self.total_duration()}/{self.time_budget_minutes} min used):"]
        for pet, task in self.scheduled_tasks:
            lines.append(f"  - [{task.priority}] {pet.name}: {task.title} ({task.duration_minutes} min)")

        conflicts = self.detect_conflicts()
        if conflicts:
            lines.append("Conflicts detected:")
            for first, second in conflicts:
                lines.append(f"  - {first.title} vs {second.title} ({first.category})")

        lines.append(f"Remaining time: {self.remaining_time()} min")
        return "\n".join(lines)
