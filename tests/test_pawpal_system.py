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


from datetime import datetime, timedelta

from pawpal_system import Category, Frequency, Owner, Priority, Scheduler

D = datetime(2026, 10, 20)


def make(*pets):
    owner = Owner("T")
    for p in pets:
        owner.add_pet(p)
    return owner, Scheduler(owner)


def test_sort_tasks_by_time_puts_undated_last():
    pet = Pet("Buddy", "dog")
    late = Task("late", due=D.replace(hour=18))
    free = Task("free")
    early = Task("early", due=D.replace(hour=8))
    for t in (late, free, early):
        pet.add_task(t)
    _, s = make(pet)
    assert [t.title for t in s.sort_tasks_by_time()] == ["early", "late", "free"]


def test_filter_by_pet_name_status_and_category():
    a, b = Pet("Buddy", "dog"), Pet("Mia", "cat")
    walk = Task("walk", category=Category.WALK)
    meds = Task("meds", category=Category.MEDS)
    a.add_task(walk)
    b.add_task(meds)
    meds.mark_complete()
    _, s = make(a, b)
    assert s.filter_tasks(pet="buddy") == [walk]
    assert s.filter_tasks(pet=b, status=True) == [meds]
    assert s.filter_tasks(status=False) == [walk]
    assert s.filter_tasks(category=Category.MEDS) == [meds]


def test_daily_recurrence_creates_next_day_task():
    pet = Pet("Buddy", "dog")
    t = Task("walk", due=D.replace(hour=8), frequency=Frequency.DAILY)
    pet.add_task(t)
    nxt = t.mark_complete()
    assert nxt.due == D.replace(hour=8) + timedelta(days=1)
    assert not nxt.completed and nxt in pet.tasks and len(pet.tasks) == 2
    assert t.mark_complete() is None  # no double-spawn


def test_late_completion_skips_past_occurrences():
    t = Task("walk", due=D.replace(hour=8), frequency=Frequency.DAILY)
    nxt = t.mark_complete(completed_at=D + timedelta(days=3, hours=9))
    assert nxt.due == D.replace(hour=8) + timedelta(days=4)


def test_non_recurring_task_spawns_nothing():
    pet = Pet("Buddy", "dog")
    t = Task("bath", due=D)
    pet.add_task(t)
    assert t.mark_complete() is None and len(pet.tasks) == 1


def test_task_conflicts_detected_across_pets_and_ignore_touching_and_undated():
    a, b = Pet("Buddy", "dog"), Pet("Mia", "cat")
    a.add_task(Task("walk", duration_minutes=30, due=D.replace(hour=8)))
    b.add_task(Task("meds", duration_minutes=5, due=D.replace(hour=8, minute=15)))
    b.add_task(Task("play", duration_minutes=10, due=D.replace(hour=8, minute=30)))
    b.add_task(Task("free"))
    _, s = make(a, b)
    pairs = s.detect_task_conflicts()
    assert [(x.title, y.title) for x, y in pairs] == [("walk", "meds")]
    assert "different pets" in s.conflict_warnings()[0]
    assert s.detect_task_conflicts(on_date=(D + timedelta(days=1)).date()) == []


def test_completed_tasks_do_not_conflict():
    a = Pet("Buddy", "dog")
    t1 = Task("x", due=D)
    a.add_task(t1)
    a.add_task(Task("y", due=D))
    t1.mark_complete()
    _, s = make(a)
    assert s.detect_task_conflicts() == []


def test_generated_schedule_has_no_overlaps():
    a = Pet("Buddy", "dog")
    a.add_task(Task("x", duration_minutes=30, due=D.replace(hour=8)))
    a.add_task(Task("y", duration_minutes=30, due=D.replace(hour=8)))
    _, s = make(a)
    s.generate_schedule(D.date())
    assert s.detect_conflicts() == []


def test_scheduler_complete_task_creates_next_weekly_occurrence():
    pet = Pet("Mia", "cat")
    t = Task("bath", due=D.replace(hour=10), frequency=Frequency.WEEKLY)
    pet.add_task(t)
    _, s = make(pet)
    nxt = s.complete_task(t, now=D.replace(hour=11))
    assert nxt.due == D.replace(hour=10) + timedelta(weeks=1)
    assert nxt.pet is pet and nxt in pet.tasks and t.completed


def test_same_pet_tasks_at_exact_same_time_are_flagged():
    pet = Pet("Buddy", "dog")
    pet.add_task(Task("walk", due=D.replace(hour=8)))
    pet.add_task(Task("feed", due=D.replace(hour=8)))
    _, s = make(pet)
    (warning,) = s.conflict_warnings()
    assert "same time" in warning and "same pet" in warning


def test_conflict_warnings_can_be_limited_to_one_pet():
    a, b, c = Pet("Max", "dog"), Pet("Maxine", "cat"), Pet("Zed", "cat")
    a.add_task(Task("x", due=D))
    b.add_task(Task("y", due=D))
    c.add_task(Task("z", due=D + timedelta(hours=5)))
    _, s = make(a, b, c)
    assert len(s.conflict_warnings(pet=a)) == 1
    assert s.conflict_warnings(pet=c) == []


def test_conflict_check_returns_warning_instead_of_crashing_on_bad_data():
    from datetime import timezone
    pet = Pet("Buddy", "dog")
    pet.add_task(Task("aware", due=D.replace(tzinfo=timezone.utc)))
    pet.add_task(Task("naive", due=D))
    _, s = make(pet)
    (warning,) = s.conflict_warnings()
    assert warning.startswith("Could not check for conflicts")


def plan(pets, budget=120, **prefs):
    owner = Owner("T", available_minutes_per_day=budget, preferences=prefs)
    for p in pets:
        owner.add_pet(p)
    s = Scheduler(owner)
    s.generate_schedule(D.date())
    return s


def test_knapsack_prefers_two_short_tasks_over_one_long_one():
    pet = Pet("Rex", "dog")
    pet.add_task(Task("long", duration_minutes=50))
    pet.add_task(Task("a", duration_minutes=25))
    pet.add_task(Task("b", duration_minutes=25))
    s = plan([pet], budget=60)
    assert sorted(i.task.title for i in s.schedule) == ["a", "b"]
    assert [t.title for t in s.skipped_tasks] == ["long"]


def test_high_priority_outweighs_several_low_tasks():
    pet = Pet("Rex", "dog")
    pet.add_task(Task("big", duration_minutes=40, priority=Priority.HIGH))
    pet.add_task(Task("l1", duration_minutes=20, priority=Priority.LOW))
    pet.add_task(Task("l2", duration_minutes=20, priority=Priority.LOW))
    s = plan([pet], budget=40)
    assert [i.task.title for i in s.schedule] == ["big"]


def test_medication_is_mandatory_even_when_low_priority():
    pet = Pet("Mia", "cat")
    pet.add_task(Task("meds", category=Category.MEDS, duration_minutes=30,
                      priority=Priority.LOW))
    pet.add_task(Task("play", duration_minutes=30, priority=Priority.HIGH))
    s = plan([pet], budget=30)
    assert [i.task.title for i in s.schedule] == ["meds"]


def test_over_budget_medication_is_kept_with_a_warning():
    pet = Pet("Mia", "cat")
    pet.add_task(Task("meds", category=Category.MEDS, duration_minutes=30))
    s = plan([pet], budget=10)
    assert len(s.schedule) == 1 and "Medication" in s.warnings[0]


def test_overdue_task_gets_a_score_boost():
    pet = Pet("Rex", "dog")
    old = Task("old", due=D - timedelta(days=1))
    new = Task("new")
    _, s = make(pet)
    assert s._score(old, D.date()) > s._score(new, D.date())


def test_dated_task_keeps_its_time_and_flexible_task_fills_the_gap():
    pet = Pet("Rex", "dog")
    pet.add_task(Task("noon", duration_minutes=30, due=D.replace(hour=12)))
    pet.add_task(Task("free", duration_minutes=30))
    s = plan([pet])
    times = {i.task.title: i.start.hour for i in s.schedule}
    assert times == {"noon": 12, "free": 8}


def test_clashing_task_shifts_to_next_free_slot_with_reason():
    pet = Pet("Rex", "dog")
    pet.add_task(Task("a", duration_minutes=30, priority=Priority.HIGH, due=D.replace(hour=9)))
    pet.add_task(Task("b", duration_minutes=30, priority=Priority.LOW, due=D.replace(hour=9)))
    s = plan([pet])
    by = {i.task.title: i for i in s.schedule}
    assert by["a"].start.hour == 9 and by["b"].start == D.replace(hour=9, minute=30)
    assert "shifted +30 min" in by["b"].reason
    assert s.detect_conflicts() == []


def test_task_beyond_delay_tolerance_is_reported_unplaced():
    pet = Pet("Rex", "dog")
    pet.add_task(Task("a", duration_minutes=120, priority=Priority.HIGH, due=D.replace(hour=9)))
    pet.add_task(Task("b", duration_minutes=10, priority=Priority.LOW, due=D.replace(hour=9)))
    s = plan([pet], budget=200, max_delay_minutes=60)
    assert [i.task.title for i in s.schedule] == ["a"]
    (task, why), = s.unplaced
    assert task.title == "b" and "within 60 min" in why


def test_unplaced_task_frees_its_gap_for_later_tasks():
    pet = Pet("Rex", "dog")
    pet.add_task(Task("a", duration_minutes=120, priority=Priority.HIGH, due=D.replace(hour=9)))
    pet.add_task(Task("b", duration_minutes=10, priority=Priority.MEDIUM, due=D.replace(hour=9)))
    pet.add_task(Task("c", duration_minutes=10, priority=Priority.LOW))
    s = plan([pet], budget=200, max_delay_minutes=60)
    starts = {i.task.title: i.start for i in s.schedule}
    assert starts["c"] == D.replace(hour=8)  # fills before the 09:00 block


def test_schedule_never_exceeds_budget_or_overlaps():
    pet = Pet("Rex", "dog")
    for i in range(8):
        pet.add_task(Task(f"t{i}", duration_minutes=10 + 7 * i,
                          priority=Priority(1 + i % 3),
                          due=D.replace(hour=8 + i % 3)))
    s = plan([pet], budget=90)
    assert sum(i.task.duration_minutes for i in s.schedule) <= 90
    assert s.detect_conflicts() == []
