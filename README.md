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

Output from running `python3 main.py`, which builds an owner with two pets (Buddy and Mia), adds five tasks, and prints the generated plan:

```
Today's Schedule · Travis · Tuesday, October 20
───────────────────────────────────────────────────────────
TIME          PET     TASK              PRIORITY   DURATION
───────────────────────────────────────────────────────────
08:00-08:30   Buddy   Morning walk      HIGH         30 min
08:30-08:35   Mia     Thyroid meds      HIGH          5 min
              ↳ due 08:15, delayed to 08:30 by earlier tasks
12:00-12:25   Mia     Playtime          MEDIUM       25 min
18:00-18:10   Buddy   Evening feeding   HIGH         10 min
18:10-18:30   Buddy   Brush coat        LOW          20 min
              ↳ flexible time
───────────────────────────────────────────────────────────
Planned 90 of 120 min  [███████████████░░░░░] 75%
```

The plan covers both pets at once. Mia's meds were due at 08:15 but start at 08:30 because Buddy's walk runs until then, and the output says so. To see one pet's tasks only, pass a name: `python3 main.py Mia`.

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

| Feature           | Method(s)                       | Notes                            |
|-------------------|---------------------------------|----------------------------------|
| Task sorting      | `_rank()`, `sort_by_priority()` | Priority first, then due time    |
| Filtering         | `_fit()`, `filter_tasks()`      | Skips tasks past the time budget |
| Conflict handling | `detect_conflicts()`            | Flags overlapping time slots     |
| Recurring tasks   | `mark_complete()`               | Daily or weekly copy per pet     |

- **Sorting:** `_rank()` orders tasks by priority (highest first), then earlier due time, with
  undated tasks last. `sort_by_time()` and `sort_by_priority()` return new lists of the planned
  items and leave the stored schedule unchanged.
- **Filtering:** `_collect_pending()` gathers pending tasks from every pet through
  `Owner.get_all_tasks()`. `_fit()` keeps tasks until the owner's time budget runs out and moves the
  rest to `skipped_tasks`. `filter_tasks()` filters by pet and/or completion status, and
  `get_schedule_for()` / `get_skipped_for()` return one pet's slice of the plan.
- **Conflicts:** `_fit()` never starts a task before the previous one ends, so tasks due at the same
  time are delayed (the reason says so). `ScheduledItem.overlaps()` and `detect_conflicts()` catch
  overlaps added or moved by hand; a generated plan has none.
- **Recurrence:** completing a `DAILY` or `WEEKLY` task adds a copy due one day or week later to the
  same pet. One-off or already-completed tasks create nothing.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
