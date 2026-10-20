import sys
from datetime import date, datetime
from typing import Optional

from pawpal_system import (
    Category,
    Frequency,
    Owner,
    Pet,
    Priority,
    Scheduler,
    Task,
)

BAR_WIDTH = 20


def at(hour: int, minute: int = 0) -> datetime:
    """A time today, so the demo always schedules for the current date."""
    return datetime.combine(date.today(), datetime.min.time()).replace(
        hour=hour, minute=minute
    )


def format_schedule(
    scheduler: Scheduler, on_date: date, pet: Optional[Pet] = None
) -> str:
    """Render the plan as a table; pass a pet to show only that pet's tasks."""
    owner = scheduler.owner
    if pet is None:
        items, skipped = scheduler.sort_by_time(), scheduler.skipped_tasks
    else:
        items, skipped = scheduler.get_schedule_for(pet), scheduler.get_skipped_for(pet)

    header = ("TIME", "PET", "TASK", "PRIORITY", "DURATION")
    rows = [
        (
            f"{i.start:%H:%M}-{i.end:%H:%M}",
            i.task.pet.name,
            i.task.title,
            i.task.priority.name,
            f"{i.task.duration_minutes} min",
        )
        for i in items
    ]
    widths = [max(len(h), *(len(r[c]) for r in rows)) if rows else len(h)
              for c, h in enumerate(header)]

    def line(cells) -> str:
        return (
            f"{cells[0]:<{widths[0]}}   {cells[1]:<{widths[1]}}   "
            f"{cells[2]:<{widths[2]}}   {cells[3]:<{widths[3]}}   "
            f"{cells[4]:>{widths[4]}}"
        )

    rule = "─" * len(line(header))
    title = f"Today's Schedule · {owner.name} · {on_date:%A, %B %d}"
    if pet is not None:
        title += f" · {pet.name} only"
    out = [title, rule, line(header), rule]

    if not rows:
        out.append("Nothing scheduled.")
    indent = " " * (widths[0] + 3)
    for item, row in zip(items, rows):
        out.append(line(row))
        # Only explain items that aren't simply on time at their due time.
        if item.task.due is None or item.start != item.task.due:
            out.append(f"{indent}↳ {item.reason}")

    out.append(rule)
    if skipped:
        out.append("Skipped (no time left)")
        out += [f"  • {t.pet.name}: {t.title} ({t.duration_minutes} min)" for t in skipped]
        out.append(rule)

    budget = owner.get_available_time(on_date)
    day_total = sum(i.task.duration_minutes for i in scheduler.schedule)
    shown = sum(i.task.duration_minutes for i in items)
    filled = round(BAR_WIDTH * day_total / budget) if budget else 0
    bar = "█" * filled + "░" * (BAR_WIDTH - filled)
    if pet is None:
        out.append(f"Planned {day_total} of {budget} min  [{bar}] "
                   f"{round(100 * day_total / budget) if budget else 0}%")
    else:
        out.append(f"{pet.name}: {shown} min planned "
                   f"(whole day: {day_total} of {budget} min  [{bar}])")
    return "\n".join(out)


def main(pet_name: Optional[str] = None) -> None:
    owner = Owner("Travis", available_minutes_per_day=120)

    buddy = Pet("Buddy", "dog", age=3)
    mia = Pet("Mia", "cat", age=5, special_needs="Daily thyroid medication")
    owner.add_pet(buddy)
    owner.add_pet(mia)

    buddy.add_task(Task("Morning walk", Category.WALK, 30, Priority.HIGH,
                        at(8), Frequency.DAILY))
    buddy.add_task(Task("Brush coat", Category.GROOMING, 20, Priority.LOW))
    buddy.add_task(Task("Evening feeding", Category.FEEDING, 10, Priority.HIGH,
                        at(18), Frequency.DAILY))
    mia.add_task(Task("Thyroid meds", Category.MEDS, 5, Priority.HIGH,
                      at(8, 15), Frequency.DAILY))
    mia.add_task(Task("Playtime", Category.PLAY, 25, Priority.MEDIUM, at(12)))

    pet = None
    if pet_name:
        pet = next((p for p in owner.pets if p.name.lower() == pet_name.lower()), None)
        if pet is None:
            names = ", ".join(p.name for p in owner.pets)
            sys.exit(f"No pet named '{pet_name}'. Pets: {names}")

    scheduler = Scheduler(owner)
    scheduler.generate_schedule(date.today())
    print(format_schedule(scheduler, date.today(), pet))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
