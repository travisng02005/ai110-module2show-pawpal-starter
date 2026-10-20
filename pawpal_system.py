from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from enum import Enum, IntEnum
from typing import Optional


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Category(Enum):
    FEEDING = "feeding"
    WALK = "walk"
    MEDS = "meds"
    GROOMING = "grooming"
    VET = "vet"
    PLAY = "play"
    GENERAL = "general"


class Frequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


_RECURRENCE_STEP = {
    Frequency.DAILY: timedelta(days=1),
    Frequency.WEEKLY: timedelta(weeks=1),
}


@dataclass
class Task:
    title: str
    category: Category = Category.GENERAL
    duration_minutes: int = 15
    priority: Priority = Priority.MEDIUM
    due: Optional[datetime] = None
    frequency: Frequency = Frequency.ONCE
    completed: bool = False
    # Back-reference set by Pet.add_task; excluded from repr/eq to avoid
    # infinite recursion (Pet -> Task -> Pet ...).
    pet: Optional["Pet"] = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    def mark_complete(self) -> Optional["Task"]:
        """Mark done; if recurring, add the next occurrence to self.pet and return it."""
        if self.completed:
            return None
        self.completed = True

        step = _RECURRENCE_STEP.get(self.frequency)
        if step is None:
            return None

        next_due = self.due + step if self.due else None
        next_task = replace(self, due=next_due, completed=False)
        if self.pet is not None:
            self.pet.add_task(next_task)
        return next_task

    def reschedule(self, new_due: datetime) -> None:
        self.due = new_due

    def is_overdue(self, now: datetime) -> bool:
        return not self.completed and self.due is not None and self.due < now

    def __str__(self) -> str:
        mark = "x" if self.completed else " "
        due = f", due {self.due:%b %d %H:%M}" if self.due else ""
        return (
            f"[{mark}] {self.title} ({self.category.value}, "
            f"{self.duration_minutes} min, {self.priority.name}{due})"
        )


@dataclass
class Pet:
    name: str
    species: str
    age: int = 0
    special_needs: str = ""
    tasks: list[Task] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.age < 0:
            raise ValueError("age cannot be negative")
        # Tasks passed to the constructor need their back-reference set too.
        for task in self.tasks:
            task.pet = self

    def add_task(self, task: Task) -> None:
        """Append the task and set task.pet = self."""
        if any(t is task for t in self.tasks):
            return
        if task.pet is not None and task.pet is not self:
            task.pet.remove_task(task)
        task.pet = self
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        # Compare by identity: dataclass == would match any identical-looking task.
        for i, t in enumerate(self.tasks):
            if t is task:
                del self.tasks[i]
                task.pet = None
                return

    def get_pending_tasks(self) -> list[Task]:
        return [t for t in self.tasks if not t.completed]

    def get_tasks_by_category(self, category: Category) -> list[Task]:
        return [t for t in self.tasks if t.category == category]


@dataclass
class Owner:
    name: str
    available_minutes_per_day: int = 120
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        if not any(p is pet for p in self.pets):
            self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        self.pets = [p for p in self.pets if p is not pet]

    def get_all_tasks(self) -> list[Task]:
        """Every pet's tasks in one list; each task's .pet says whose it is."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_available_time(self, on_date: date) -> int:
        """Minutes available for pet care on the given date."""
        return self.available_minutes_per_day


@dataclass
class ScheduledItem:
    task: Task
    start: datetime
    end: datetime
    reason: str = ""

    def overlaps(self, other: "ScheduledItem") -> bool:
        return self.start < other.end and other.start < self.end


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.schedule: list[ScheduledItem] = []
        self.skipped_tasks: list[Task] = []

    def generate_schedule(self, on_date: date) -> list[ScheduledItem]:
        """Clear previous state, then collect, sort, fit, and explain."""
        self.schedule = []
        self.skipped_tasks = []
        self._fit(self._rank(self._collect_pending(on_date)), on_date)
        return self.schedule

    def detect_conflicts(self) -> list[tuple[ScheduledItem, ScheduledItem]]:
        """Pairs of scheduled items whose time ranges overlap."""
        items = self.sort_by_time()
        return [
            (a, b)
            for i, a in enumerate(items)
            for b in items[i + 1:]
            if a.overlaps(b)
        ]

    def sort_by_time(self) -> list[ScheduledItem]:
        return sorted(self.schedule, key=lambda item: item.start)

    def sort_by_priority(self) -> list[ScheduledItem]:
        return sorted(
            self.schedule, key=lambda item: (-item.task.priority, item.start)
        )

    def get_schedule_for(self, pet: Pet) -> list[ScheduledItem]:
        """One pet's slice of the plan, in time order."""
        return [item for item in self.sort_by_time() if item.task.pet is pet]

    def get_skipped_for(self, pet: Pet) -> list[Task]:
        return [task for task in self.skipped_tasks if task.pet is pet]

    def filter_tasks(
        self, pet: Optional[Pet] = None, status: Optional[bool] = None
    ) -> list[Task]:
        """Filter across all pets by pet and/or completion (True = done)."""
        return [
            task
            for task in self.owner.get_all_tasks()
            if (pet is None or task.pet is pet)
            and (status is None or task.completed == status)
        ]

    def explain_plan(self) -> str:
        if not self.schedule and not self.skipped_tasks:
            return "Nothing to schedule."
        lines = []
        for item in self.sort_by_time():
            pet = item.task.pet.name if item.task.pet else "?"
            lines.append(
                f"{item.start:%H:%M}-{item.end:%H:%M}  {pet}: "
                f"{item.task.title} ({item.task.priority.name} priority, {item.reason})"
            )
        for task in self.skipped_tasks:
            pet = task.pet.name if task.pet else "?"
            lines.append(
                f"SKIPPED  {pet}: {task.title} "
                f"({task.duration_minutes} min did not fit in the time budget)"
            )
        return "\n".join(lines)

    def get_next_task(self, now: datetime) -> Optional[ScheduledItem]:
        """The current or next unfinished item that hasn't ended yet."""
        for item in self.sort_by_time():
            if not item.task.completed and item.end > now:
                return item
        return None

    # Private helpers so generate_schedule's steps can be tested separately.
    def _collect_pending(self, on_date: date) -> list[Task]:
        """Pending tasks from every pet (via the owner) due on or before on_date."""
        return [
            task
            for task in self.owner.get_all_tasks()
            if not task.completed and (task.due is None or task.due.date() <= on_date)
        ]

    def _rank(self, tasks: list[Task]) -> list[Task]:
        """Highest priority first; earlier due time breaks ties, undated last."""
        return sorted(tasks, key=lambda t: (-t.priority, t.due or datetime.max))

    def _fit(self, tasks: list[Task], on_date: date) -> None:
        """Pick ranked tasks that fit the budget, then lay them out in time order."""
        budget = self.owner.get_available_time(on_date)
        chosen, used = [], 0
        for task in tasks:
            if used + task.duration_minutes <= budget:
                chosen.append(task)
                used += task.duration_minutes
            else:
                self.skipped_tasks.append(task)

        day_start = self.owner.preferences.get("day_start", time(8, 0))
        cursor = datetime.combine(on_date, day_start)
        chosen.sort(key=lambda t: (t.due or datetime.max, -t.priority))
        for task in chosen:
            start = max(cursor, task.due) if task.due else cursor
            end = start + timedelta(minutes=task.duration_minutes)
            self.schedule.append(
                ScheduledItem(task, start, end, self._reason(task, start, on_date))
            )
            cursor = end

    @staticmethod
    def _reason(task: Task, start: datetime, on_date: date) -> str:
        parts = []
        if task.due is None:
            parts.append("flexible time")
        elif task.due.date() < on_date:
            parts.append("overdue from an earlier day")
        else:
            parts.append(f"due {task.due:%H:%M}")
            if start > task.due:
                parts.append(f"delayed to {start:%H:%M} by earlier tasks")
        return ", ".join(parts)
