from datetime import date

from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    owner = Owner(name="Jamie Rivera", contact_info="jamie@example.com")

    dog = Pet(name="Rex", species="Dog", breed="Labrador", age=3)
    cat = Pet(name="Whiskers", species="Cat", breed="Tabby", age=5)
    owner.add_pet(dog)
    owner.add_pet(cat)

    today = date.today()

    feed_dog = Task(
        title="Feed Rex",
        category="feeding",
        duration_minutes=15,
        priority="high",
        recurrence="daily",
        next_due_date=today,
    )
    walk_dog = Task(
        title="Walk Rex",
        category="exercise",
        duration_minutes=30,
        priority="medium",
        recurrence="daily",
        next_due_date=today,
    )
    feed_cat = Task(
        title="Feed Whiskers",
        category="feeding",
        duration_minutes=10,
        priority="high",
        recurrence="daily",
        next_due_date=today,
    )

    dog.add_task(feed_dog)
    dog.add_task(walk_dog)
    cat.add_task(feed_cat)

    scheduler = Scheduler.build(owner, today, available_minutes=90)

    print("Today's Schedule")
    print("=================")
    print(scheduler.explain())


if __name__ == "__main__":
    main()
