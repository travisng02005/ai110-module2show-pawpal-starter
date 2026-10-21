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
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

| Feature           | Method(s)                                    | Notes                                         |
|-------------------|----------------------------------------------|-----------------------------------------------|
| Task ranking      | `_rank()`, `sort_by_priority()`              | Priority first, then due time                 |
| Task selection    | `_score()`, `_select()`                      | Knapsack: best total score within the budget  |
| Time placement    | `_place()`                                   | Free-gap list; bounded shift for clashes      |
| Filtering         | `filter_tasks()`, `sort_tasks_by_time()`     | By pet, status, category                      |
| Conflict warnings | `conflict_warnings()`, `detect_conflicts()`  | Warns about clashing requested times          |
| Recurring tasks   | `mark_complete()`, `complete_task()`         | Daily or weekly copy per pet                  |

- **Selection:** `_score()` values a task at 10 per priority level, plus 15 if it is overdue from an
  earlier day. `_select()` solves a 0/1 knapsack over minutes by dynamic programming, so two short
  tasks can beat one long one of equal priority. Medication tasks are mandatory: they are always
  chosen, and if they alone exceed the budget the plan keeps them and adds a warning. Tasks left out
  go to `skipped_tasks`.
- **Placement:** `_place()` tracks free time as a list of gaps. Dated tasks go first, highest
  priority first, at their due time; a clash moves a task to the next free slot, and the reason says
  by how much. A task that would shift more than `preferences["max_delay_minutes"]` (default 60) is
  recorded in `unplaced` with a reason instead. Undated tasks then fill the earliest remaining gaps.
### Sorting

- `Scheduler.sort_by_time()` returns the planned items ordered by start time (a new list).
- `Scheduler.sort_by_priority()` returns planned items highest priority first, ties broken by start time.
- `Scheduler.sort_tasks_by_time(tasks=None)` orders raw tasks (default: all pets') by due time, with
  undated tasks last.

### Filtering

- `Scheduler.filter_tasks(pet, status, category)` filters across all pets. `pet` can be a `Pet` or a
  case-insensitive name, `status` is `True` (done) / `False` (pending), and `category` is a `Category`.
  Any argument left as `None` is ignored.
- `Scheduler.get_schedule_for(pet)` returns one pet's planned items in time order, and
  `Scheduler.get_skipped_for(pet)` returns that pet's tasks that did not fit the time budget.

### Conflict detection

- `Task.window()` gives a task's `(start, end)` from its due time and duration, and
  `Task.conflicts_with(other)` is true when two dated tasks' windows overlap.
- `Scheduler.detect_task_conflicts(on_date=None)` compares all pending dated tasks across every pet
  (optionally for one day) and returns the clashing pairs.
- `Scheduler.conflict_warnings(on_date=None, pet=None)` turns those pairs into readable messages,
  labelled "same pet" or "different pets". It never raises: bad data such as mixed timezone-aware and
  naive datetimes yields a warning string instead.
- The scheduler moves tasks apart, so a generated plan has no overlaps. `Scheduler.detect_conflicts()`
  (using `ScheduledItem.overlaps()`) is a safety check on the finished plan.

### Recurring tasks

- `Task.mark_complete(completed_at=None)` marks the task done. For a `DAILY` or `WEEKLY` task it adds a
  copy due one day or week later to the same pet and returns it. If `completed_at` is given and the
  task was finished late, the due date keeps stepping forward until it is in the future.
- One-off tasks, and tasks that are already completed, create nothing.
- `Scheduler.complete_task(task, now=None)` is the scheduler-level entry point; it calls
  `mark_complete()` with the current time.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
