import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pawpal_system import Pet, Task


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
