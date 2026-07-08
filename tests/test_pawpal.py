import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pawpal_system import Owner, Pet, Task, Scheduler


def test_mark_complete_changes_task_status():
    task = Task(title="Feed", category="feeding", duration_minutes=10, priority="high")
    assert task.completed is False

    task.mark_complete(date(2026, 1, 1))

    assert task.completed is True
    assert task.last_completed_date == date(2026, 1, 1)


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Rex", species="dog", breed="Labrador", age=3)
    assert len(pet.get_tasks()) == 0

    task = Task(title="Walk", category="exercise", duration_minutes=20, priority="medium")
    pet.add_task(task)

    assert len(pet.get_tasks()) == 1
    assert task in pet.get_tasks()


def test_sort_by_time_returns_chronological_order():
    scheduler = Scheduler(date=date(2026, 1, 1), owner=Owner(name="Jamie", contact_info="j@example.com"), time_budget_minutes=60)

    evening = Task(title="Evening walk", category="exercise", duration_minutes=20, priority="medium", scheduled_time="18:00")
    morning = Task(title="Morning walk", category="exercise", duration_minutes=20, priority="medium", scheduled_time="07:30")
    midday = Task(title="Lunch", category="feeding", duration_minutes=10, priority="high", scheduled_time="12:00")
    unscheduled = Task(title="Groom", category="grooming", duration_minutes=45, priority="low")

    ordered = scheduler.sort_by_time([evening, morning, midday, unscheduled])

    assert [task.title for task in ordered] == ["Morning walk", "Lunch", "Evening walk", "Groom"]


def test_mark_complete_on_daily_task_creates_next_day_occurrence():
    pet = Pet(name="Rex", species="dog", breed="Labrador", age=3)
    task = Task(
        title="Feed",
        category="feeding",
        duration_minutes=10,
        priority="high",
        recurrence="daily",
        next_due_date=date(2026, 1, 1),
    )
    pet.add_task(task)

    next_task = task.mark_complete(date(2026, 1, 1))

    assert task.completed is True
    assert task.next_due_date is None
    assert next_task is not None
    assert next_task.title == "Feed"
    assert next_task.next_due_date == date(2026, 1, 1) + timedelta(days=1)
    assert next_task in pet.get_tasks()


def test_detect_time_conflicts_flags_duplicate_scheduled_times():
    owner = Owner(name="Jamie", contact_info="j@example.com")
    dog = Pet(name="Rex", species="dog", breed="Labrador", age=3)
    cat = Pet(name="Whiskers", species="cat", breed="Tabby", age=5)
    owner.add_pet(dog)
    owner.add_pet(cat)

    walk = Task(
        title="Walk Rex",
        category="exercise",
        duration_minutes=30,
        priority="medium",
        next_due_date=date(2026, 1, 1),
        scheduled_time="07:30",
    )
    meds = Task(
        title="Morning Meds",
        category="medical",
        duration_minutes=10,
        priority="high",
        next_due_date=date(2026, 1, 1),
        scheduled_time="07:30",
    )
    dog.add_task(walk)
    cat.add_task(meds)

    scheduler = Scheduler.build(owner, date(2026, 1, 1), available_minutes=60)
    warnings = scheduler.detect_time_conflicts()

    assert len(warnings) == 1
    assert "Walk Rex" in warnings[0]
    assert "Morning Meds" in warnings[0]
    assert "07:30" in warnings[0]
