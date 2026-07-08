from datetime import date

from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    owner = Owner(name="Jamie Rivera", contact_info="jamie@example.com")

    dog = Pet(name="Rex", species="Dog", breed="Labrador", age=3)
    cat = Pet(name="Whiskers", species="Cat", breed="Tabby", age=5)
    owner.add_pet(dog)
    owner.add_pet(cat)

    today = date.today()

    # Tasks are deliberately created and added out of chronological and
    # priority order, to prove sort_by_time/sort_by_priority actually sort
    # rather than just echoing insertion order.
    feed_dog = Task(
        title="Feed Rex",
        category="feeding",
        duration_minutes=15,
        priority="high",
        recurrence="daily",
        next_due_date=today,
        scheduled_time="18:00",
    )
    groom_dog = Task(
        title="Groom Rex",
        category="grooming",
        duration_minutes=45,
        priority="low",
        recurrence=None,
        completed=True,
        scheduled_time="12:00",
    )
    walk_dog = Task(
        title="Walk Rex",
        category="exercise",
        duration_minutes=30,
        priority="medium",
        recurrence="daily",
        next_due_date=today,
        scheduled_time="07:30",
    )
    play_cat = Task(
        title="Play with Whiskers",
        category="exercise",
        duration_minutes=20,
        priority="low",
        recurrence="daily",
        next_due_date=today,
        scheduled_time="20:15",
    )
    feed_cat = Task(
        title="Feed Whiskers",
        category="feeding",
        duration_minutes=10,
        priority="high",
        recurrence="daily",
        next_due_date=today,
        scheduled_time="08:00",
    )
    # Deliberately collides with walk_dog's 07:30 slot, across two different
    # pets, to exercise the new time-conflict detection.
    meds_cat = Task(
        title="Morning Meds",
        category="medical",
        duration_minutes=10,
        priority="high",
        recurrence="daily",
        next_due_date=today,
        scheduled_time="07:30",
    )

    dog.add_task(feed_dog)
    dog.add_task(groom_dog)
    dog.add_task(walk_dog)
    cat.add_task(play_cat)
    cat.add_task(feed_cat)
    cat.add_task(meds_cat)

    scheduler = Scheduler.build(owner, today, available_minutes=90)

    print("Today's Schedule")
    print("=================")
    print(scheduler.explain())

    print("\nTasks sorted by time of day (earliest first)")
    print("=============================================")
    for task in scheduler.sort_by_time(owner.get_all_tasks()):
        print(f"  - {task.scheduled_time}  {task.title}")

    print("\nTasks sorted by priority (highest first)")
    print("=========================================")
    for task in scheduler.sort_by_priority(owner.get_all_tasks()):
        print(f"  - [{task.priority}] {task.title}")

    print("\nRex's tasks")
    print("===========")
    for task in owner.filter_tasks(pet_name="Rex"):
        print(f"  - {task.title}")

    print("\nIncomplete tasks")
    print("================")
    for task in owner.filter_tasks(completed=False):
        print(f"  - {task.title}")

    print("\nCompleted tasks")
    print("===============")
    for task in owner.filter_tasks(completed=True):
        print(f"  - {task.title}")

    print("\nRex's incomplete tasks")
    print("======================")
    for task in owner.filter_tasks(pet_name="Rex", completed=False):
        print(f"  - {task.title}")

    next_feed_dog = feed_dog.mark_complete(today)
    print(f"\nAfter completing '{feed_dog.title}':")
    print(f"  - original instance: completed={feed_dog.completed}, next_due_date={feed_dog.next_due_date}")
    if next_feed_dog is not None:
        print(f"  - new instance created: '{next_feed_dog.title}', next_due_date={next_feed_dog.next_due_date}")
    print(f"  - Rex now has {len(dog.get_tasks())} tasks on file")


if __name__ == "__main__":
    main()
