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

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

Today's Schedule
=================
Schedule for 2026-07-07 (55/90 min used):
  - [high] Rex: Feed Rex (15 min)
  - [high] Whiskers: Feed Whiskers (10 min)
  - [medium] Rex: Walk Rex (30 min)
Remaining time: 35 min

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
================================================================================================== test session starts ===================================================================================================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Travis\Documents\VSCode\ai110-module2show-pawpal-starter
plugins: anyio-4.14.0
collected 5 items                                                                                                                                                                                                         

tests\test_pawpal.py .....                                                                                                                                                                                          [100%]

=================================================================================================== 5 passed in 0.03s ====================================================================================================
```
Confidence level 5
1. test_mark_complete_changes_task_status — completing a task flips completed to True and records last_completed_date.
2. test_adding_task_increases_pet_task_count — adding a task to a pet updates its task list/count.
3. test_sort_by_time_returns_chronological_order — Scheduler.sort_by_time orders tasks earliest-to-latest by scheduled_time, with unscheduled tasks pushed to the end.
4. test_mark_complete_on_daily_task_creates_next_day_occurrence — recurrence logic: completing a daily task finalizes the original (cleared next_due_date) and spawns a new Task due one day later, attached to the same pet.
5. test_detect_time_conflicts_flags_duplicate_scheduled_times — Scheduler.build + detect_time_conflicts flags two tasks from different pets/categories scheduled at the same time, with a warning naming both tasks and the time.

## ✨ Features

- **Priority-based sorting** — `Scheduler.sort_by_priority()` orders tasks high → medium → low.
- **Chronological sorting** — `Scheduler.sort_by_time()` orders tasks by `scheduled_time` (earliest first), pushing unscheduled tasks to the end.
- **Task filtering** — `Owner.filter_tasks()` (and its `get_tasks_by_pet()` / `get_tasks_by_status()` wrappers) narrow tasks by pet name and/or completion status.
- **Time-budget fitting** — `Scheduler.filter_by_time()` greedily fills the available minutes in priority order, dropping tasks that no longer fit.
- **Category conflict detection** — `Scheduler.detect_conflicts()` flags scheduled tasks that share the same pet and category (e.g., two feedings for the same pet).
- **Time-slot conflict warnings** — `Scheduler.detect_time_conflicts()` flags any two scheduled tasks (across all pets) sharing the same `scheduled_time`, returning warning strings instead of raising.
- **Daily/weekly/monthly recurrence** — `Task.is_recurring` + `Task.mark_complete()` finalize the completed instance and automatically spawn the next occurrence on the correct due date.
- **Due/overdue tracking** — `Task.is_due()` / `Task.is_overdue()` and `Pet.get_tasks_due_on()` determine which tasks belong in today's schedule.
- **Human-readable plan summary** — `Scheduler.explain()` renders the schedule, time budget usage, and any conflicts as a single readable report.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_priority()`, `Scheduler.sort_by_time()` | `sort_by_priority` orders tasks high → medium → low for building today's schedule. `sort_by_time` orders tasks by `scheduled_time` ("HH:MM", earliest first); tasks with no `scheduled_time` sort to the end. |
| Filtering | `Owner.filter_tasks()`, `Owner.get_tasks_by_pet()`, `Owner.get_tasks_by_status()`, `Scheduler.filter_by_time()` | `filter_tasks` narrows tasks by pet name and/or completion status (either or both). `get_tasks_by_pet`/`get_tasks_by_status` are thin wrappers around it. `filter_by_time` greedily keeps tasks (in priority order) until the time budget runs out, dropping any that don't fit. |
| Conflict handling | `Scheduler.detect_conflicts()`, `Scheduler.detect_time_conflicts()` | `detect_conflicts` flags scheduled tasks that share the same pet + category (e.g., two feeding tasks for the same pet). `detect_time_conflicts` is a lightweight exact-match check across *all* pets for tasks sharing the same `scheduled_time`; it returns warning strings (see `Scheduler.explain()`) instead of raising, so a scheduling clash never crashes the app. |
| Recurring tasks | `Task.is_recurring`, `Task.mark_complete()`, `Pet.get_recurring_tasks()` | Recurrence is tracked via `Task.recurrence` ("daily", "weekly", or "monthly"). Calling `mark_complete()` finalizes the current instance as a completed historical record and, if recurring, automatically creates and attaches a new `Task` instance for the next due date. |

## 📸 Demo Walkthrough

### Main UI features

The Streamlit app (`app.py`) is organized into four sections:

- **Owner** — enter the owner's name and contact info; this is stored once in `st.session_state` so it persists across reruns.
- **Add a Pet** — enter a pet's name, species, breed, and age, then click **Add pet**. Added pets show up in a running table below the form.
- **Add a Task** — pick one of the owner's pets from a dropdown, then set a title, category, duration, priority, optional recurrence, and next due date, and click **Add task**. A radio filter (All / Pending / Completed) lets you narrow the task table by completion status.
- **Build Schedule** — pick a schedule date and a time budget (in minutes), then click **Generate schedule**. This produces a table of the tasks that were fit into the budget, "Time used" / "Time remaining" metrics, and any conflict warnings.

### Example workflow

1. Fill in the owner fields (or accept the defaults) at the top of the page.
2. Add a pet, e.g. "Mochi" the dog — it appears in the pets table.
3. Add a task for Mochi, e.g. "Morning walk," 20 minutes, high priority, due today — it appears in the tasks table.
4. Click **Generate schedule** for today's date with a time budget (e.g. 60 minutes).
5. Review the generated schedule: which tasks made the cut, how much time was used/remaining, and whether any conflicts were flagged.

### Key Scheduler behaviors shown

- **Priority + time sorting** — the schedule table orders tasks by priority first, then by `scheduled_time` within that.
- **Time-budget fitting** — only as many due tasks as fit the budget (greedily, in priority order) are scheduled; the rest are left out.
- **Conflict warnings** — if two scheduled tasks share the same pet + category (e.g., two feeding tasks for the same pet), or two tasks across any pets share the same `scheduled_time`, a warning is shown instead of the app crashing.
- **Recurrence** — completing a recurring task (daily/weekly/monthly) automatically creates its next occurrence with an updated due date.

### Sample CLI output (`python main.py`)

```
Today's Schedule
=================
Schedule for 2026-07-08 (85/90 min used):
  - [high] Rex: Feed Rex (15 min)
  - [high] Whiskers: Feed Whiskers (10 min)
  - [high] Whiskers: Morning Meds (10 min)
  - [medium] Rex: Walk Rex (30 min)
  - [low] Whiskers: Play with Whiskers (20 min)
Warning: 'Morning Meds' (Whiskers) and 'Walk Rex' (Rex) are both scheduled at 07:30.
Remaining time: 5 min

Tasks sorted by time of day (earliest first)
=============================================
  - 07:30  Walk Rex
  - 07:30  Morning Meds
  - 08:00  Feed Whiskers
  - 12:00  Groom Rex
  - 18:00  Feed Rex
  - 20:15  Play with Whiskers

Tasks sorted by priority (highest first)
=========================================
  - [high] Feed Rex
  - [high] Feed Whiskers
  - [high] Morning Meds
  - [medium] Walk Rex
  - [low] Groom Rex
  - [low] Play with Whiskers

Rex's tasks
===========
  - Feed Rex
  - Groom Rex
  - Walk Rex

Incomplete tasks
================
  - Feed Rex
  - Walk Rex
  - Play with Whiskers
  - Feed Whiskers
  - Morning Meds

Completed tasks
===============
  - Groom Rex

Rex's incomplete tasks
======================
  - Feed Rex
  - Walk Rex

After completing 'Feed Rex':
  - original instance: completed=True, next_due_date=None
  - new instance created: 'Feed Rex', next_due_date=2026-07-09
  - Rex now has 4 tasks on file
```

*(Dates above reflect running `main.py` on 2026-07-08 — `today` is computed at run time, so your output will show the current date instead.)*

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
