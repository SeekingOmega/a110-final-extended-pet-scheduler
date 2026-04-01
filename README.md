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

### Smarter Scheduling

**Sorting & Filtering**
- `Task` gained a `time: str` field for scheduled start time in `"HH:MM"` format
- `Scheduler.sort_tasks_by_time()` — sorts all tasks using a lambda key; tasks without a time sink to the bottom
- `Scheduler.filter_tasks(completed, pet_name)` — filter by completion status and/or pet name; both parameters are optional
- UI: "View Task List" section with Sort by, Filter by status, and Filter by pet dropdowns

---

**Recurring Tasks**
- `"as_needed"` frequency renamed to `"once"`
- `Task` gained a `due_date: str` field (`"YYYY-MM-DD"`)
- `Task.next_occurrence()` — returns a new `Task` for the next recurrence using `timedelta` (daily = +1 day, weekly = +7 days, once = None)
- `Scheduler.handle_completion(pet, task)` — marks a task done and automatically adds the next occurrence to the pet's task list
- UI: due date input in the task form; checking "Done" in the table calls `handle_completion`

---

**Task Deletion**
- `Pet.remove_task()` method added
- UI: 🗑️ checkbox column in the task table — checking it immediately removes the task

---

**Conflict Detection**
- `Scheduler.get_conflicts()` — groups pending tasks by time slot and returns any slot with 2+ tasks
- `Scheduler.generate_plan()` updated with a `booked_slots` set — only the highest-priority task per time slot makes it into the plan; conflicting tasks are skipped
- `Scheduler.get_summary()` refactored to delegate to `generate_plan()` so both are always in sync
- Schedule output now prints the date and time of each task (`@ 2026-04-01 | 08:00`)
- UI: conflict warnings are shown separately from "didn't fit" warnings, explaining which task won and which was omitted
