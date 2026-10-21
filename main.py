import argparse
import sys
from datetime import date, datetime, time
from typing import Optional

from pawpal_system import (
    Category,
    Frequency,
    Owner,
    Pet,
    Priority,
    ScheduledItem,
    Scheduler,
    Task,
)

BAR_WIDTH = 20
COLUMNS = (("TIME", "<"), ("PET", "<"), ("TASK", "<"), ("PRIORITY", "<"), ("DURATION", ">"))
SEP = "   "


def at(on_date: date, hour: int, minute: int = 0) -> datetime:
    """A datetime on the given date."""
    return datetime.combine(on_date, time(hour, minute))


def build_demo_owner(on_date: date, budget: int = 120) -> Owner:
    """Sample owner with two pets and five tasks, due relative to on_date."""
    owner = Owner("Travis", available_minutes_per_day=budget)
    buddy = Pet("Buddy", "dog", age=3)
    mia = Pet("Mia", "cat", age=5, special_needs="Daily thyroid medication")
    owner.add_pet(buddy)
    owner.add_pet(mia)

    # Deliberately added out of order (evening first, flexible tasks mixed in) so
    # the sorting and filtering views have something to untangle.
    buddy.add_task(Task("Evening feeding", category=Category.FEEDING, duration_minutes=10,
                        priority=Priority.HIGH, due=at(on_date, 18),
                        frequency=Frequency.DAILY))
    mia.add_task(Task("Playtime", category=Category.PLAY, duration_minutes=25,
                      priority=Priority.MEDIUM, due=at(on_date, 12)))
    buddy.add_task(Task("Brush coat", category=Category.GROOMING, duration_minutes=20,
                        priority=Priority.LOW))
    mia.add_task(Task("Thyroid meds", category=Category.MEDS, duration_minutes=5,
                      priority=Priority.HIGH, due=at(on_date, 8, 15),
                      frequency=Frequency.DAILY))
    buddy.add_task(Task("Morning walk", category=Category.WALK, duration_minutes=30,
                        priority=Priority.HIGH, due=at(on_date, 8),
                        frequency=Frequency.DAILY))
    # Same due time as Buddy's walk, to demonstrate conflict warnings.
    mia.add_task(Task("Breakfast", category=Category.FEEDING, duration_minutes=10,
                      priority=Priority.HIGH, due=at(on_date, 8),
                      frequency=Frequency.DAILY))
    return owner


def find_pet(owner: Owner, name: str) -> Pet:
    """Case-insensitive pet lookup; raises LookupError if missing or ambiguous."""
    matches = [p for p in owner.pets if p.name.lower() == name.lower()]
    if len(matches) == 1:
        return matches[0]
    names = ", ".join(p.name for p in owner.pets)
    if not matches:
        raise LookupError(f"No pet named '{name}'. Pets: {names}")
    raise LookupError(f"{len(matches)} pets are named '{name}'; names must be unique.")


def pet_name(task: Task) -> str:
    """The task's pet name, or '?' for an unattached task."""
    return task.pet.name if task.pet else "?"


def needs_explanation(item: ScheduledItem) -> bool:
    """Only items not simply on time at their due time get a reason line."""
    return item.task.due is None or item.start != item.task.due


def percent(part: int, whole: int) -> int:
    """Whole-number percentage, 0 when whole is 0."""
    return round(100 * part / whole) if whole else 0


def progress_bar(part: int, whole: int) -> str:
    """Fixed-width bar filled in proportion to part/whole."""
    filled = min(BAR_WIDTH, round(BAR_WIDTH * part / whole)) if whole else 0
    return "█" * filled + "░" * (BAR_WIDTH - filled)


def schedule_rows(items: list[ScheduledItem]) -> list[tuple[str, ...]]:
    """One display row per scheduled item, matching COLUMNS."""
    return [
        (
            f"{i.start:%H:%M}-{i.end:%H:%M}",
            pet_name(i.task),
            i.task.title,
            i.task.priority.name,
            f"{i.task.duration_minutes} min",
        )
        for i in items
    ]


def render_table(rows: list[tuple[str, ...]]) -> tuple[list[str], list[str], int]:
    """Format header and rows to aligned lines; returns (header, rows, indent)."""
    widths = [
        max(len(h), *(len(r[c]) for r in rows)) if rows else len(h)
        for c, (h, _) in enumerate(COLUMNS)
    ]

    def line(cells) -> str:
        return SEP.join(
            f"{cell:{align}{w}}" for cell, (_, align), w in zip(cells, COLUMNS, widths)
        )

    return (
        [line([h for h, _ in COLUMNS])],
        [line(r) for r in rows],
        widths[0] + len(SEP),
    )


def format_footer(scheduler: Scheduler, items: list[ScheduledItem],
                  on_date: date, pet: Optional[Pet]) -> str:
    """Time-budget summary, plus the pet's own share when filtered."""
    budget = scheduler.owner.get_available_time(on_date)
    day_total = sum(i.task.duration_minutes for i in scheduler.schedule)
    bar = progress_bar(day_total, budget)
    if pet is None:
        return f"Planned {day_total} of {budget} min  [{bar}] {percent(day_total, budget)}%"
    shown = sum(i.task.duration_minutes for i in items)
    return f"{pet.name}: {shown} min planned (whole day: {day_total} of {budget} min  [{bar}])"


def format_schedule(
    scheduler: Scheduler, on_date: date, pet: Optional[Pet] = None
) -> str:
    """Render the plan as a table; pass a pet to show only that pet's tasks."""
    if pet is None:
        items, skipped = scheduler.sort_by_time(), scheduler.skipped_tasks
    else:
        items, skipped = scheduler.get_schedule_for(pet), scheduler.get_skipped_for(pet)

    header, body, indent = render_table(schedule_rows(items))
    rule = "─" * len(header[0])
    day = "Today's" if on_date == date.today() else f"{on_date:%b %d}"
    title = f"{day} Schedule · {scheduler.owner.name} · {on_date:%A, %B %d}"
    if pet is not None:
        title += f" · {pet.name} only"

    out = [title, rule, *header, rule]
    if not body:
        out.append("Nothing scheduled.")
    for item, text in zip(items, body):
        out.append(text)
        if needs_explanation(item):
            out.append(f"{' ' * indent}↳ {item.reason}")
    out.append(rule)

    if skipped:
        out.append("Skipped (no time left)")
        out += [f"  • {pet_name(t)}: {t.title} ({t.duration_minutes} min)" for t in skipped]
        out.append(rule)

    unplaced = [(t, why) for t, why in scheduler.unplaced if pet is None or t.pet is pet]
    if unplaced:
        out.append("Could not be placed")
        out += [f"  • {pet_name(t)}: {t.title} ({why})" for t, why in unplaced]
        out.append(rule)

    out.append(format_footer(scheduler, items, on_date, pet))
    out += [f"⚠ {w}" for w in scheduler.warnings]

    warnings = scheduler.conflict_warnings(on_date, pet)
    if warnings:
        out.append("")
        out += [f"⚠ {w}" for w in warnings]
    return "\n".join(out)


def format_extras(scheduler: Scheduler, now: datetime) -> str:
    """Exercise the rest of the system: conflicts, next task, filters, recurrence."""
    out = ["", "Extras", "──────"]

    warnings = scheduler.conflict_warnings(now.date())
    out.append(f"Conflicts: {len(warnings)} requested-time, "
               f"{len(scheduler.detect_conflicts())} in plan")
    out += [f"  ⚠ {w}" for w in warnings]

    out.append("Pending by due time: " + ", ".join(
        t.title for t in scheduler.sort_tasks_by_time(scheduler.filter_tasks(status=False))))

    nxt = scheduler.get_next_task(now)
    out.append(f"Next up after {now:%H:%M}: "
               + (f"{nxt.task.title} at {nxt.start:%H:%M}" if nxt else "nothing"))

    first = scheduler.sort_by_time()[:1]
    if first:
        task = first[0].task
        follow_up = task.mark_complete(completed_at=now)
        out.append(f"Completed '{task.title}'"
                   + (f" -> next occurrence due {follow_up.due:%b %d %H:%M}"
                      if follow_up and follow_up.due else " (not recurring)"))

    done = len(scheduler.filter_tasks(status=True))
    pending = len(scheduler.filter_tasks(status=False))
    out.append(f"Tasks done: {done}, pending: {pending}")
    return "\n".join(out)


def format_views(scheduler: Scheduler) -> str:
    """Show tasks in the order they were added, then via sorting and filtering."""
    def titles(tasks: list[Task]) -> str:
        return ", ".join(f"{t.title} ({pet_name(t)})" for t in tasks) or "none"

    owner = scheduler.owner
    out = ["", "Sorting & filtering", "───────────────────",
           f"As added:          {titles(owner.get_all_tasks())}",
           f"Sorted by time:    {titles(scheduler.sort_tasks_by_time())}"]
    for p in owner.pets:
        out.append(f"{p.name} only:".ljust(19)
                   + titles(scheduler.sort_tasks_by_time(scheduler.filter_tasks(pet=p.name))))
    out += [f"Done:              {titles(scheduler.filter_tasks(status=True))}",
            f"Pending:           {titles(scheduler.sort_tasks_by_time(scheduler.filter_tasks(status=False)))}",
            f"Mia, pending:      {titles(scheduler.filter_tasks(pet='mia', status=False))}",
            f"Meds category:     {titles(scheduler.filter_tasks(category=Category.MEDS))}"]
    return "\n".join(out)


def format_selection_demo(on_date: date) -> str:
    """Show the knapsack picking better than a priority-order greedy pass."""
    owner = Owner("Demo", available_minutes_per_day=60)
    pet = Pet("Rex", "dog")
    owner.add_pet(pet)
    for title, minutes in [("Long hike", 50), ("Short walk", 25), ("Brush teeth", 25)]:
        pet.add_task(Task(title, duration_minutes=minutes, priority=Priority.MEDIUM))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule(on_date)

    greedy, used = [], 0  # what taking tasks in rank order would have done
    for t in scheduler._rank(scheduler.owner.get_all_tasks()):
        if used + t.duration_minutes <= 60:
            greedy.append(t)
            used += t.duration_minutes
    score = lambda tasks: sum(scheduler._score(t, on_date) for t in tasks)
    picked = [i.task for i in scheduler.schedule]
    names = lambda tasks: ", ".join(t.title for t in tasks)
    return "\n".join([
        "", "Selection demo (60 min budget, three MEDIUM tasks)", "─" * 48,
        f"Greedy would pick:    {names(greedy)} (score {score(greedy)})",
        f"Knapsack picks:       {names(picked)} (score {score(picked)})",
    ])


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PawPal+ terminal schedule demo.")
    parser.add_argument("pet", nargs="?", help="show only this pet's tasks")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today(),
                        metavar="YYYY-MM-DD", help="day to plan (default: today)")
    parser.add_argument("--budget", type=int, default=120, metavar="MIN",
                        help="available minutes for the day (default: 120)")
    parser.add_argument("--list-pets", action="store_true", help="list pets and exit")
    parser.add_argument("--extras", action="store_true",
                        help="also show conflicts, next task and recurrence demo")
    args = parser.parse_args(argv)
    if args.budget <= 0:
        parser.error("--budget must be positive")
    return args


def main(argv: Optional[list[str]] = None) -> None:
    # Box-drawing characters need UTF-8; Windows consoles often default otherwise.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args(argv)
    owner = build_demo_owner(args.date, args.budget)

    if args.list_pets:
        for p in owner.pets:
            print(f"{p.name} ({p.species}, age {p.age}): {len(p.tasks)} tasks")
        return

    try:
        pet = find_pet(owner, args.pet) if args.pet else None
    except LookupError as err:
        sys.exit(str(err))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule(args.date)
    print(format_schedule(scheduler, args.date, pet))
    if args.extras:
        print(format_extras(scheduler, at(args.date, 9)))
        print(format_views(scheduler))
        print(format_selection_demo(args.date))


if __name__ == "__main__":
    main()
