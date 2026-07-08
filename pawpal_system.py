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

    def get_tasks_by_pet(self, pet: Pet) -> list[Task]:
        """Return all of this owner's tasks belonging to a specific pet."""
        return self.filter_tasks(pet_name=pet.name)

    def get_tasks_by_status(self, completed: bool) -> list[Task]:
        """Return all of this owner's tasks matching the given completion status."""
        return self.filter_tasks(completed=completed)

    def filter_tasks(self, pet_name: str | None = None, completed: bool | None = None) -> list[Task]:
        """Return this owner's tasks filtered by pet name and/or completion status.

        Either filter may be omitted; passing both narrows by both criteria.

        Args:
            pet_name: If given, only keep tasks belonging to the pet with this name.
            completed: If given, only keep tasks whose completed flag matches.

        Returns:
            The subset of get_all_tasks() matching every filter that was given.
        """
        tasks = self.get_all_tasks()
        if pet_name is not None:
            tasks = [task for task in tasks if task.pet is not None and task.pet.name == pet_name]
        if completed is not None:
            tasks = [task for task in tasks if task.completed == completed]
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

    def get_recurring_tasks(self) -> list[Task]:
        """Return this pet's recurring tasks.

        Returns:
            Every task on this pet whose recurrence is one of the known
            schedules (daily/weekly/monthly), regardless of due/completed state.
        """
        return [task for task in self.tasks if task.is_recurring]


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
    scheduled_time: str | None = None  # "HH:MM", 24-hour

    @property
    def is_recurring(self) -> bool:
        """Return whether this task repeats on a known recurrence schedule.

        Returns:
            True if recurrence is "daily", "weekly", or "monthly"; False otherwise
            (including None or an unrecognized value).
        """
        return self.recurrence in _RECURRENCE_DAYS

    def mark_complete(self, completed_date: date | None = None) -> Task | None:
        """Mark this task complete and, if recurring, spawn its next occurrence.

        This instance is finalized as a completed historical record. If the
        task recurs (daily/weekly/monthly), a new Task instance is created for
        the next due date, attached to the same pet, and returned. Returns
        None for one-off tasks.

        Args:
            completed_date: The date the task was completed on. Defaults to
                this task's next_due_date, or today if that is also unset.

        Returns:
            The newly created Task for the next occurrence, or None if this
            task does not recur.
        """
        completed_date = completed_date or self.next_due_date or date.today()
        self.completed = True
        self.last_completed_date = completed_date
        self.next_due_date = None

        recurrence_days = _RECURRENCE_DAYS.get(self.recurrence)
        if recurrence_days is None:
            return None

        next_task = Task(
            title=self.title,
            category=self.category,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            recurrence=self.recurrence,
            next_due_date=completed_date + timedelta(days=recurrence_days),
            scheduled_time=self.scheduled_time,
        )
        if self.pet is not None:
            self.pet.add_task(next_task)
        return next_task

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

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return the tasks sorted by scheduled time of day, earliest first.

        Tasks with no scheduled_time are sorted to the end.

        Args:
            tasks: The tasks to sort. Not mutated.

        Returns:
            A new list of the same tasks in ascending scheduled_time order.
        """
        def time_key(task: Task) -> tuple[int, int, int]:
            if task.scheduled_time is None:
                return (1, 0, 0)
            hours, minutes = task.scheduled_time.split(":")
            return (0, int(hours), int(minutes))

        return sorted(tasks, key=time_key)

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

    def detect_time_conflicts(self) -> list[str]:
        """Return warning messages for scheduled tasks that share a scheduled_time.

        This is a lightweight exact-match check on scheduled_time (not a full
        overlapping-duration calculation), and it checks across all pets, not
        just within one. Tasks with no scheduled_time are skipped rather than
        treated as conflicting with each other. Returns warning strings instead
        of raising, so a scheduling clash never crashes the program.

        Returns:
            One warning string per colliding pair of scheduled tasks (empty if
            no two scheduled tasks share a scheduled_time).
        """
        warnings = []
        seen: dict[str, tuple[Pet, Task]] = {}
        for pet, task in self.scheduled_tasks:
            if task.scheduled_time is None:
                continue
            existing = seen.get(task.scheduled_time)
            if existing is not None:
                existing_pet, existing_task = existing
                warnings.append(
                    f"Warning: '{existing_task.title}' ({existing_pet.name}) and "
                    f"'{task.title}' ({pet.name}) are both scheduled at {task.scheduled_time}."
                )
            else:
                seen[task.scheduled_time] = (pet, task)
        return warnings

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

        for warning in self.detect_time_conflicts():
            lines.append(warning)

        lines.append(f"Remaining time: {self.remaining_time()} min")
        return "\n".join(lines)
