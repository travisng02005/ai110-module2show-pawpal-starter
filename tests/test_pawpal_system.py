from pawpal_system import Pet, Task


def test_mark_complete_changes_task_status():
    task = Task("Morning walk")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_to_pet_increases_task_count():
    pet = Pet("Buddy", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Morning walk"))

    assert len(pet.tasks) == 1
