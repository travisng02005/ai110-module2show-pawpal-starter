# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## ✨ Features

- **Multi-pet planning:** one owner, any number of pets. A single plan covers every pet's tasks, and
  each task remembers which pet it belongs to.
- **Sorting by time:** planned items sort by start time, and raw tasks sort by due time with
  flexible (undated) tasks last.
- **Sorting by priority:** the plan can be ordered highest priority first, with ties broken by start
  time.
- **Filtering:** tasks filter by pet (object or case-insensitive name), by completion status and by
  category, and the plan can be viewed one pet at a time.
- **Best-fit task selection:** a 0/1 knapsack (dynamic programming over minutes) picks the set of
  tasks with the highest total score that fits the owner's daily time budget, so two short tasks can
  beat one long task of equal priority. Priority sets the score, and tasks overdue from an earlier
  day get a bonus.
- **Mandatory medication:** `meds` tasks are always scheduled. If they alone exceed the budget, the
  plan keeps them and shows a warning.
- **Gap-based placement:** tasks go on a timeline of free gaps. A task keeps its requested time if it
  is free, otherwise it shifts to the next free slot, and the plan explains the shift ("due 08:00,
  shifted +30 min to 08:30").
- **Bounded delay:** a task that would shift more than `max_delay_minutes` (default 60) is reported
  as unplaced, with the reason, instead of being pushed to a time that no longer makes sense.
- **Conflict warnings:** tasks whose requested times overlap, including exact duplicates, produce a
  readable warning labelled "same pet" or "different pets". The check never crashes on bad data.
  Back-to-back tasks are not conflicts.
- **Overlap-free plans:** a generated plan never has overlapping tasks, and a separate check
  confirms it.
- **Daily and weekly recurrence:** completing a recurring task creates the next occurrence on the
  same pet, one day or one week later. A task finished late skips forward to a future date, and a
  task can't spawn twice.
- **Skipped-task reporting:** tasks that don't fit the budget are listed as skipped, per pet or
  overall.
- **Plan explanations:** every planned item carries a reason, and the plan can be printed as plain
  text.
- **Streamlit app:** add and edit pets, add tasks, mark tasks complete (completed tasks move to their
  own list), and generate the day's plan with metrics, a time-budget bar and warnings.

## 🖥️ Sample Output

Output from running `python3 main.py`, which builds an owner with two pets (Buddy and Mia), adds six tasks (Buddy's walk and Mia's breakfast are deliberately due at the same time), and prints the generated plan:

```
Today's Schedule · Travis · Tuesday, October 20
───────────────────────────────────────────────────────────
TIME          PET     TASK              PRIORITY   DURATION
───────────────────────────────────────────────────────────
08:00-08:30   Buddy   Morning walk      HIGH         30 min
08:30-08:40   Mia     Breakfast         HIGH         10 min
              ↳ due 08:00, shifted +30 min to 08:30 (slot taken)
08:40-08:45   Mia     Thyroid meds      HIGH          5 min
              ↳ due 08:15, shifted +25 min to 08:40 (slot taken)
08:45-09:05   Buddy   Brush coat        LOW          20 min
              ↳ flexible time
12:00-12:25   Mia     Playtime          MEDIUM       25 min
18:00-18:10   Buddy   Evening feeding   HIGH         10 min
───────────────────────────────────────────────────────────
Planned 100 of 120 min  [█████████████████░░░] 83%

⚠ Buddy: Morning walk (08:00) is at the same time as Mia: Breakfast (08:00) [different pets]
⚠ Buddy: Morning walk (08:00) overlaps Mia: Thyroid meds (08:15) [different pets]
```

The plan covers both pets at once. Breakfast and the meds were due at 08:00 and 08:15 but start later because Buddy's walk runs until 08:30, and the output says so. The warnings under the table flag tasks whose requested times clash; the scheduler still places every task, just later. To see one pet's tasks only, pass a name: `python3 main.py Mia`.

## 🧪 Testing PawPal+

```bash
# Run the full test suite
pytest

# Run with coverage (needs: pip install pytest-cov)
pytest --cov=pawpal_system
```

Sample output:

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\Travis\Documents\VSCode\AI110\ai110-module2show-pawpal-starter
configfile: pytest.ini
testpaths: tests
collected 26 items

tests\test_pawpal_system.py ..........................                 [100%]

============================= 26 passed in 0.06s ==============================
```

**Confidence level:** 4

## 📐 Smarter Scheduling

PawPal+ does more than sort a list. It picks the best set of tasks for the day, places them without
overlaps, warns about clashes, and keeps recurring tasks going. All of it lives in `Scheduler`
([pawpal_system.py](pawpal_system.py)) and `Task`.

| Feature            | What it does                                        | Methods                                                                |
|--------------------|-----------------------------------------------------|------------------------------------------------------------------------|
| **Sorting**        | Orders plans and tasks by time or priority          | `sort_by_time()`, `sort_by_priority()`, `sort_tasks_by_time()`         |
| **Filtering**      | Narrows tasks and plans by pet, status or category  | `filter_tasks()`, `get_schedule_for()`, `get_skipped_for()`            |
| **Conflicts**      | Flags tasks whose requested times overlap           | `detect_task_conflicts()`, `conflict_warnings()`, `detect_conflicts()` |
| **Recurring**      | Creates the next daily or weekly task on completion | `Task.mark_complete()`, `complete_task()`                              |
| **Task selection** | Chooses the highest-value tasks that fit the budget | `_score()`, `_select()`                                                |
| **Placement**      | Puts chosen tasks on the timeline, avoiding clashes | `_place()`                                                             |

### Sorting

| Method                           | Returns                                                    |
|----------------------------------|------------------------------------------------------------|
| `sort_by_time()`                 | Planned items by start time                                |
| `sort_by_priority()`             | Planned items, highest priority first (ties by start time) |
| `sort_tasks_by_time(tasks=None)` | Raw tasks by due time (default: all pets'), undated last   |

All three return new lists and leave the plan itself unchanged.

### Filtering

- `filter_tasks(pet, status, category)` filters across all pets. `pet` is a `Pet` or a
  case-insensitive name, `status` is `True` (done) or `False` (pending), and `category` is a
  `Category`. Any argument left as `None` is ignored.
- `get_schedule_for(pet)` returns one pet's planned items in time order.
- `get_skipped_for(pet)` returns that pet's tasks that did not fit the time budget.

### Conflict detection

- `Task.window()` and `Task.conflicts_with(other)` test whether two dated tasks overlap. Tasks that
  only touch (one ends as the next starts) do not conflict, and undated tasks never do.
- `detect_task_conflicts(on_date=None)` compares all pending dated tasks across every pet and
  returns the clashing pairs.
- `conflict_warnings(on_date=None, pet=None)` turns those pairs into readable messages, labelled
  "same pet" or "different pets". It never raises: bad data, such as mixed timezone-aware and naive
  datetimes, returns a warning message instead.
- The scheduler moves tasks apart, so a generated plan has no overlaps.
  `detect_conflicts()` (using `ScheduledItem.overlaps()`) double-checks the finished plan.

### Recurring tasks

- `Task.mark_complete(completed_at=None)` marks the task done. A `DAILY` or `WEEKLY` task adds a copy
  due one day or week later to the same pet and returns it.
- If the task was finished late, the due date keeps stepping forward until it is in the future.
- One-off tasks, and tasks that are already completed, create nothing.
- `Scheduler.complete_task(task, now=None)` is the scheduler-level entry point; it calls
  `mark_complete()` with the current time.

### Task selection

`_score()` values a task at 10 per priority level, plus 15 if it is overdue from an earlier day.
`_select()` then solves a 0/1 knapsack over minutes by dynamic programming, so two short tasks can
beat one long task of equal priority.

- Medication tasks are mandatory. They are always chosen, and if they alone exceed the budget the
  plan keeps them and adds a warning.
- Tasks left out go to `skipped_tasks`.

### Placement

`_place()` tracks free time as a list of gaps.

1. Dated tasks go first, highest priority first, at their due time. A clash moves a task to the next
   free slot, and the plan's reason says by how much.
2. A task that would shift more than `preferences["max_delay_minutes"]` (default 60) is recorded in
   `unplaced` with a reason instead.
3. Undated tasks then fill the earliest remaining gaps.


## 📸 Demo Walkthrough

Start the app with `streamlit run app.py`. The page runs top to bottom: owner and pets, tasks, then the schedule.

### What you can do in the app

| Area | Actions |
|------|---------|
| **Owner and pets** | Set the owner's name and the minutes available per day. Add a pet (name, species, age) and edit its details in the "Edit a pet" panel. Duplicate or blank names are rejected. |
| **Tasks** | Add a task for a pet with a category, duration, priority, repeat (once, daily or weekly) and an optional requested time. Filter the list by pet. |
| **Pending and completed** | Pending tasks are listed by time. Pick one and click "Complete task" to move it to the "Completed" list. A repeating task also adds its next occurrence. |
| **Conflict check** | A warning appears whenever two requested times overlap, before any plan exists. A green message appears when there are none. |
| **Build schedule** | "Generate schedule" builds the day's plan. View it by time or by priority, for all pets or one, and read each task's reason. |

### Example workflow

1. **Add a pet:** under "Owner and pets", enter *Mochi*, choose *dog*, and click "Add pet". Add a second pet, *Mia*, the same way.
2. **Add tasks:** under "Tasks", add *Morning walk* for Mochi (30 min, high priority, tick "Request a time", 08:00, repeats daily). Add *Breakfast* for Mia at 08:00 too, and *Brush coat* for Mochi with no requested time.
3. **Read the warning:** a conflict warning appears: *Mochi: Morning walk (08:00) is at the same time as Mia: Breakfast (08:00)*.
4. **Generate the schedule:** click "Generate schedule". The metrics show how many tasks were planned and how much of the time budget is used.
5. **View today's plan:** the table lists each task in time order. Breakfast moves to 08:30 and its reason says *due 08:00, shifted +30 min to 08:30 (slot taken)*. Switch "Order by" to Priority, or pick one pet.
6. **Complete a task:** mark *Morning walk* complete. It moves to "Completed", and tomorrow's walk appears in the pending list. The old plan is cleared, so click "Generate schedule" again.

### Scheduler behaviors on display

- **Sorting:** pending tasks sort by requested time with flexible tasks last, and the plan sorts by start time or by priority.
- **Filtering:** the task list filters by pet, and the plan can be shown for one pet. Completed tasks are split from pending ones.
- **Conflict warnings:** overlapping requests are flagged as "same pet" or "different pets", including exact duplicate times.
- **Conflict resolution:** the generated plan never overlaps. Clashing tasks shift to the next free slot, and a task that would shift too far is reported as unplaced.
- **Best-fit selection:** tasks that don't fit the time budget are listed as skipped, and medication tasks are always kept.
- **Recurrence:** completing a daily or weekly task creates the next one automatically.

### Command-line demo

`python main.py` runs the same scheduler without the UI. It builds an owner with two pets, deliberately
gives two tasks the same requested time, and prints the plan with the conflict warnings:

```
Today's Schedule · Travis · Tuesday, October 20
───────────────────────────────────────────────────────────
TIME          PET     TASK              PRIORITY   DURATION
───────────────────────────────────────────────────────────
08:00-08:30   Buddy   Morning walk      HIGH         30 min
08:30-08:40   Mia     Breakfast         HIGH         10 min
              ↳ due 08:00, shifted +30 min to 08:30 (slot taken)
08:40-08:45   Mia     Thyroid meds      HIGH          5 min
              ↳ due 08:15, shifted +25 min to 08:40 (slot taken)
08:45-09:05   Buddy   Brush coat        LOW          20 min
              ↳ flexible time
12:00-12:25   Mia     Playtime          MEDIUM       25 min
18:00-18:10   Buddy   Evening feeding   HIGH         10 min
───────────────────────────────────────────────────────────
Planned 100 of 120 min  [█████████████████░░░] 83%

⚠ Buddy: Morning walk (08:00) is at the same time as Mia: Breakfast (08:00) [different pets]
⚠ Buddy: Morning walk (08:00) overlaps Mia: Thyroid meds (08:15) [different pets]
```

Pass a pet's name to see only that pet: `python main.py Mia`.
