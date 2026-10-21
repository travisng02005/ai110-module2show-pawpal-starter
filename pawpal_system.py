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


PRIORITY_WEIGHT = 10
OVERDUE_BONUS = 15
DEFAULT_MAX_DELAY_MINUTES = 60

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
        """Reject non-positive durations at creation time."""
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    def mark_complete(self, completed_at: Optional[datetime] = None) -> Optional["Task"]:
        """Mark done; if recurring, add the next occurrence to self.pet and return it.

        The next due time steps forward from this one. If completed_at is given and
        the task was finished late, it keeps stepping until the next occurrence is
        in the future, so a skipped day never leaves a stale due date behind.
        """
        if self.completed:
            return None
        self.completed = True

        step = _RECURRENCE_STEP.get(self.frequency)
        if step is None:
            return None

        next_due = self.due + step if self.due else None
        if next_due is not None and completed_at is not None:
            while next_due <= completed_at:
                next_due += step
        next_task = replace(self, due=next_due, completed=False)
        if self.pet is not None:
            self.pet.add_task(next_task)
        return next_task

    def reschedule(self, new_due: datetime) -> None:
        """Move the task's due time to new_due."""
        self.due = new_due

    def is_overdue(self, now: datetime) -> bool:
        """True if the task is unfinished and its due time has passed."""
        return not self.completed and self.due is not None and self.due < now

    def window(self) -> Optional[tuple[datetime, datetime]]:
        """(start, end) the task occupies if done at its due time; None if undated."""
        if self.due is None:
            return None
        return self.due, self.due + timedelta(minutes=self.duration_minutes)

    def conflicts_with(self, other: "Task") -> bool:
        """True if both tasks are dated and their due-time windows overlap."""
        a, b = self.window(), other.window()
        return a is not None and b is not None and a[0] < b[1] and b[0] < a[1]

    def __str__(self) -> str:
        """One-line summary like '[ ] Walk (walk, 30 min, HIGH, due Oct 20 08:00)'."""
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
        """Validate age and link any constructor-supplied tasks to this pet."""
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
        """Remove the task (matched by identity) and clear its pet link."""
        # Compare by identity: dataclass == would match any identical-looking task.
        for i, t in enumerate(self.tasks):
            if t is task:
                del self.tasks[i]
                task.pet = None
                return

    def get_pending_tasks(self) -> list[Task]:
        """Tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]

    def get_tasks_by_category(self, category: Category) -> list[Task]:
        """Tasks belonging to the given category."""
        return [t for t in self.tasks if t.category == category]


@dataclass
class Owner:
    name: str
    available_minutes_per_day: int = 120
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner, ignoring duplicates."""
        if not any(p is pet for p in self.pets):
            self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet (matched by identity) from this owner."""
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
        """True if the two items' time ranges intersect."""
        return self.start < other.end and other.start < self.end


class Scheduler:
    def __init__(self, owner: Owner):
        """Create a scheduler that plans from the given owner's pets' tasks."""
        self.owner = owner
        self.schedule: list[ScheduledItem] = []
        self.skipped_tasks: list[Task] = []
        # Selected tasks that found no free slot, with the reason why.
        self.unplaced: list[tuple[Task, str]] = []
        self.warnings: list[str] = []

    def generate_schedule(self, on_date: date) -> list[ScheduledItem]:
        """Clear previous state, then collect, rank, select, and place."""
        self.schedule = []
        self.skipped_tasks = []
        self.unplaced = []
        self.warnings = []
        ranked = self._rank(self._collect_pending(on_date))
        self._place(self._select(ranked, on_date), on_date)
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
        """Scheduled items ordered by start time (returns a new list)."""
        return sorted(self.schedule, key=lambda item: item.start)

    def sort_tasks_by_time(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Tasks (default: all pets') ordered by due time, undated last (new list)."""
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return sorted(tasks, key=lambda t: (t.due is None, t.due or datetime.min))

    def detect_task_conflicts(
        self, on_date: Optional[date] = None
    ) -> list[tuple[Task, Task]]:
        """Pending tasks whose due-time windows overlap, across all pets.

        The scheduler slides tasks apart, so this flags the requests that cannot
        all happen at their asked-for times. Pass on_date to check a single day.
        """
        tasks = [
            t
            for t in self.sort_tasks_by_time(self.filter_tasks(status=False))
            if t.due is not None and (on_date is None or t.due.date() == on_date)
        ]
        return [
            (a, b)
            for i, a in enumerate(tasks)
            for b in tasks[i + 1:]
            if a.conflicts_with(b)
        ]

    def conflict_warnings(
        self, on_date: Optional[date] = None, pet: Optional[Pet] = None
    ) -> list[str]:
        """Human-readable warnings for detect_task_conflicts; never raises.

        Pass pet to keep only conflicts involving that pet. Bad data (e.g. mixing
        timezone-aware and naive datetimes) yields a warning instead of an error.
        """
        try:
            pairs = self.detect_task_conflicts(on_date)
        except (TypeError, ValueError) as err:
            return [f"Could not check for conflicts: {err}"]
        warnings = []
        for a, b in pairs:
            if pet is not None and a.pet is not pet and b.pet is not pet:
                continue
            kind = "same pet" if a.pet is b.pet else "different pets"
            verb = "is at the same time as" if a.due == b.due else "overlaps"
            warnings.append(
                f"{a.pet.name if a.pet else '?'}: {a.title} ({a.due:%H:%M}) {verb} "
                f"{b.pet.name if b.pet else '?'}: {b.title} ({b.due:%H:%M}) [{kind}]"
            )
        return warnings

    def sort_by_priority(self) -> list[ScheduledItem]:
        """Scheduled items ordered highest priority first (returns a new list)."""
        return sorted(
            self.schedule, key=lambda item: (-item.task.priority, item.start)
        )

    def get_schedule_for(self, pet: Pet) -> list[ScheduledItem]:
        """One pet's slice of the plan, in time order."""
        return [item for item in self.sort_by_time() if item.task.pet is pet]

    def get_skipped_for(self, pet: Pet) -> list[Task]:
        """Tasks for one pet that didn't fit in the time budget."""
        return [task for task in self.skipped_tasks if task.pet is pet]

    def filter_tasks(
        self,
        pet: Optional[Pet | str] = None,
        status: Optional[bool] = None,
        category: Optional[Category] = None,
    ) -> list[Task]:
        """Filter across all pets by pet (object or name), completion (True = done)
        and/or category."""
        if isinstance(pet, str):
            name = pet.lower()
            match = lambda t: t.pet is not None and t.pet.name.lower() == name
        else:
            match = lambda t: pet is None or t.pet is pet
        return [
            task
            for task in self.owner.get_all_tasks()
            if match(task)
            and (status is None or task.completed == status)
            and (category is None or task.category == category)
        ]

    def explain_plan(self) -> str:
        """Plain-text plan: one line per item with its reason, then skipped tasks."""
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

    def complete_task(self, task: Task, now: Optional[datetime] = None) -> Optional[Task]:
        """Complete a task (default time: now); returns the new occurrence if recurring."""
        return task.mark_complete(completed_at=now or datetime.now())

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

    def _score(self, task: Task, on_date: date) -> int:
        """Value of doing the task today, used as the knapsack "profit".

        score = priority * PRIORITY_WEIGHT, plus OVERDUE_BONUS if the task was due
        on an earlier day than on_date. Tasks due today (even if the time has
        passed) and undated tasks get no bonus.

        Returns an int so totals are exact and ties are real ties.
        """
        score = int(task.priority) * PRIORITY_WEIGHT
        if task.due is not None and task.due.date() < on_date:
            score += OVERDUE_BONUS
        return score

    def _select(self, tasks: list[Task], on_date: date) -> list[Task]:
        """Choose the highest-scoring set of tasks that fits the time budget.

        Algorithm:
          1. Medication tasks (Category.MEDS) are mandatory and always chosen;
             their minutes are subtracted from the budget first. If they alone
             exceed it, they are all kept, the remaining budget becomes 0, and a
             message is added to self.warnings.
          2. The other tasks form a 0/1 knapsack: weight = duration in minutes,
             profit = _score(). Dynamic programming over minutes finds the set
             with the greatest total score, so several short tasks can beat one
             long task of equal priority (a greedy pass would not).
          3. Tasks not chosen are appended to self.skipped_tasks, in rank order.

        Args:
            tasks: candidate tasks, already ranked (ties keep this order, so
                earlier tasks win equal-score alternatives).
            on_date: the day being planned; sets the budget and overdue bonus.

        Returns:
            The chosen tasks: mandatory ones first, then the rest in rank order.

        Complexity: O(n * remaining_minutes) time for n optional tasks.
        """
        budget = self.owner.get_available_time(on_date)
        mandatory = [t for t in tasks if t.category is Category.MEDS]
        optional = [t for t in tasks if t.category is not Category.MEDS]

        remaining = budget - sum(t.duration_minutes for t in mandatory)
        if remaining < 0:
            self.warnings.append(
                f"Medication tasks alone need {budget - remaining} min "
                f"but only {budget} min are available."
            )
            remaining = 0

        # best[m] = (total score, chosen tasks) using at most m minutes.
        best: list[tuple[int, list[Task]]] = [(0, [])] * (remaining + 1)
        for task in optional:
            d, value = task.duration_minutes, self._score(task, on_date)
            for m in range(remaining, d - 1, -1):  # downward: each task used once
                candidate = best[m - d][0] + value
                if candidate > best[m][0]:
                    best[m] = (candidate, best[m - d][1] + [task])

        picked = {id(t) for t in best[remaining][1]}
        chosen = mandatory + [t for t in optional if id(t) in picked]
        chosen_ids = {id(t) for t in chosen}
        self.skipped_tasks += [t for t in tasks if id(t) not in chosen_ids]
        return chosen

    def _place(self, chosen: list[Task], on_date: date) -> None:
        """Put chosen tasks on the timeline using a list of free gaps.

        Free time starts as one gap from the owner's day_start (preference,
        default 08:00) to midnight. Tasks are then placed in this order:
          1. Dated tasks, highest priority first (ties by due time). Each goes at
             its due time, or at the earliest free slot after it. A task due
             before the day starts, or on an earlier day, is treated as wanting
             day_start.
          2. Undated tasks, highest priority first, into the earliest gap that
             fits. They have no delay limit.
        A dated task whose slot would be more than the tolerance after its
        desired time (preferences["max_delay_minutes"], default
        DEFAULT_MAX_DELAY_MINUTES) is not placed; its slot is released and it is
        recorded in self.unplaced with the reason. A task for which no gap fits at
        all is recorded the same way. Placed tasks are appended to self.schedule
        as ScheduledItems, sorted by start time.

        Args:
            chosen: tasks already selected by _select (their total fits the budget).
            on_date: the day being planned.

        Complexity: O(n * g) for n tasks and g gaps; g never exceeds n + 1.
        """
        day_start = datetime.combine(
            on_date, self.owner.preferences.get("day_start", time(8, 0))
        )
        day_end = datetime.combine(on_date + timedelta(days=1), time(0, 0))
        tolerance = timedelta(minutes=self.owner.preferences.get(
            "max_delay_minutes", DEFAULT_MAX_DELAY_MINUTES
        ))
        gaps = [(day_start, day_end)]

        dated = sorted((t for t in chosen if t.due), key=lambda t: (-t.priority, t.due))
        flexible = sorted((t for t in chosen if not t.due), key=lambda t: -t.priority)

        for task in dated + flexible:
            desired = max(task.due, day_start) if task.due else day_start
            start = self._take_slot(gaps, desired, task.duration_minutes)
            if start is None:
                self.unplaced.append((task, "no free slot left in the day"))
            elif task.due and start - desired > tolerance:
                self._give_back(gaps, start, task.duration_minutes)
                self.unplaced.append((task, (
                    f"no free slot within {int(tolerance.total_seconds() // 60)} min "
                    f"of {desired:%H:%M}"
                )))
            else:
                end = start + timedelta(minutes=task.duration_minutes)
                self.schedule.append(
                    ScheduledItem(task, start, end, self._reason(task, start, on_date))
                )
        self.schedule.sort(key=lambda item: item.start)

    @staticmethod
    def _take_slot(gaps: list, desired: datetime, minutes: int) -> Optional[datetime]:
        """Claim the earliest slot of `minutes` starting at or after `desired`.

        Args:
            gaps: sorted, non-overlapping (start, end) free intervals.
            desired: the earliest acceptable start time.
            minutes: length of the slot needed.

        Returns:
            The start of the claimed slot, or None if no gap can hold it.

        Mutates gaps: the claimed time is removed, which shrinks the gap or splits
        it in two (the free time before and after the slot).
        """
        need = timedelta(minutes=minutes)
        for i, (gap_start, gap_end) in enumerate(gaps):
            start = max(gap_start, desired)
            if start + need <= gap_end:
                end = start + need
                pieces = []
                if gap_start < start:
                    pieces.append((gap_start, start))
                if end < gap_end:
                    pieces.append((end, gap_end))
                gaps[i:i + 1] = pieces
                return start
        return None

    @staticmethod
    def _give_back(gaps: list, start: datetime, minutes: int) -> None:
        """Undo a _take_slot: return the slot to the free list.

        Args:
            gaps: sorted, non-overlapping (start, end) free intervals; mutated.
            start: start of the slot being released.
            minutes: length of the slot being released.

        The slot is merged with any adjacent gaps, so the list stays sorted and
        non-overlapping, and releasing a slot restores the original gap exactly.
        """
        gaps.append((start, start + timedelta(minutes=minutes)))
        gaps.sort()
        merged = [gaps[0]]
        for gap_start, gap_end in gaps[1:]:
            if gap_start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], gap_end))
            else:
                merged.append((gap_start, gap_end))
        gaps[:] = merged

    @staticmethod
    def _reason(task: Task, start: datetime, on_date: date) -> str:
        """Short explanation of how the task's due time shaped its placement.

        Returns one of: "flexible time" (no due time), "overdue from an earlier
        day", "due HH:MM, shifted +N min to HH:MM (slot taken)" when the task
        started after its due time, or "due HH:MM" when it is on time.
        """
        if task.due is None:
            return "flexible time"
        if task.due.date() < on_date:
            return "overdue from an earlier day"
        if start > task.due:
            shift = int((start - task.due).total_seconds() // 60)
            return f"due {task.due:%H:%M}, shifted +{shift} min to {start:%H:%M} (slot taken)"
        return f"due {task.due:%H:%M}"
