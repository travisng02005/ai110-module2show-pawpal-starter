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
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_priority()`, `Scheduler.sort_by_time()` | `sort_by_priority` orders tasks high → medium → low for building today's schedule. `sort_by_time` orders tasks by `scheduled_time` ("HH:MM", earliest first); tasks with no `scheduled_time` sort to the end. |
| Filtering | `Owner.filter_tasks()`, `Owner.get_tasks_by_pet()`, `Owner.get_tasks_by_status()`, `Scheduler.filter_by_time()` | `filter_tasks` narrows tasks by pet name and/or completion status (either or both). `get_tasks_by_pet`/`get_tasks_by_status` are thin wrappers around it. `filter_by_time` greedily keeps tasks (in priority order) until the time budget runs out, dropping any that don't fit. |
| Conflict handling | `Scheduler.detect_conflicts()`, `Scheduler.detect_time_conflicts()` | `detect_conflicts` flags scheduled tasks that share the same pet + category (e.g., two feeding tasks for the same pet). `detect_time_conflicts` is a lightweight exact-match check across *all* pets for tasks sharing the same `scheduled_time`; it returns warning strings (see `Scheduler.explain()`) instead of raising, so a scheduling clash never crashes the app. |
| Recurring tasks | `Task.is_recurring`, `Task.mark_complete()`, `Pet.get_recurring_tasks()` | Recurrence is tracked via `Task.recurrence` ("daily", "weekly", or "monthly"). Calling `mark_complete()` finalizes the current instance as a completed historical record and, if recurring, automatically creates and attaches a new `Task` instance for the next due date. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
