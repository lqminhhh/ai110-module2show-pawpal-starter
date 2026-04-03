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

## Features

### Owner & Pet Management
- **Owner profile** — Set your name and the total minutes you have available for pet care each day. This becomes the capacity constraint the scheduler respects.
- **Multi-pet support** — Register as many pets as you like. Each pet maintains its own independent task list.

### Task Management
- **Flexible task creation** — Every task has a title, duration, priority (Low / Medium / High), and frequency (daily, weekly, or as-needed).
- **Completion tracking** — Mark individual tasks as done. Pending and completed counts are displayed as live metrics so you always know where you stand.
- **Daily recurrence** — Marking a daily or weekly task complete automatically queues a fresh copy for the next occurrence using Python's `timedelta`. One-off (`as_needed`) tasks do not recur.

### Smart Scheduling
- **Priority-first greedy scheduling** — `Scheduler.generate()` sorts tasks by priority (High → Medium → Low) then by duration (shorter tasks first as a tiebreaker) and fills the day greedily until available time runs out.
- **Frequency filtering** — Tasks with a `weekly` frequency only appear on Mondays. Daily and as-needed tasks appear every day. The scheduler automatically skips tasks that are not due today.
- **Chronological display** — `Scheduler.sort_by_time()` uses `sorted()` with a lambda key on `start_minute` to guarantee the displayed plan always reads earliest-to-latest, regardless of the order tasks were entered.
- **Skipped task reporting** — Any task that could not fit within available time is listed with a plain-language explanation and a suggestion to adjust durations or extend the time window.

### Conflict Detection
- **Overlap warnings** — `Scheduler.detect_conflicts()` scans the generated schedule for any two items whose time windows overlap using the condition `a.start < b.end AND b.start < a.end`. Conflicts are surfaced as a prominent red error block in the UI, listing every overlapping pair with their exact times so the owner knows exactly what to fix before starting their day.
- **Non-crashing** — Warnings are returned as strings rather than exceptions, so the app always remains usable even when conflicts exist.

### Filtering & Visibility
- **Per-pet task filter** — In multi-pet households, filter the schedule view down to a single pet's tasks with one click.
- **Pending / completed split** — `Owner.get_tasks_by_status()` powers a live to-do vs. done breakdown so completed tasks never clutter the active plan.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Testing PawPal+

### Run the tests

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| Test | Area |
|------|------|
| `test_mark_complete_changes_status` | Task completion flips `completed` to `True` |
| `test_add_task_increases_pet_task_count` | Adding a task grows the pet's task list |
| `test_sort_by_time_returns_chronological_order` | Tasks added out of order are returned earliest-first |
| `test_sort_by_time_does_not_mutate_original` | `sort_by_time()` returns a new list, leaving the original untouched |
| `test_daily_task_mark_complete_creates_next_occurrence` | Daily tasks auto-spawn a fresh, incomplete next occurrence |
| `test_weekly_task_mark_complete_creates_next_occurrence` | Weekly tasks do the same |
| `test_as_needed_task_mark_complete_returns_none` | One-off tasks produce no automatic recurrence |
| `test_detect_conflicts_flags_overlapping_tasks` | Overlapping time windows are caught and reported |
| `test_detect_conflicts_no_warning_for_sequential_tasks` | Back-to-back tasks are not falsely flagged |
| `test_detect_conflicts_exact_same_start_time` | Two tasks at the exact same start minute are flagged |

### Confidence Level

**4 / 5 stars**

The core scheduling behaviors — task completion, pet task management, chronological sorting, recurring task logic, and conflict detection — are all covered and passing. One star is withheld because the following edge cases are not yet tested: available-time capacity limits (scheduler skips tasks when time runs out), frequency filtering by day of week (`due_today()`), and the full `generate()` end-to-end flow with a real Owner/Pet/Scheduler stack.

## Smarter Scheduling

PawPal+ goes beyond a basic task list with four algorithmic improvements:

- **Sort by time** — `Scheduler.sort_by_time()` uses `sorted()` with a lambda key on `start_minute` to return scheduled items in chronological order, so the displayed plan always reads top-to-bottom from earliest to latest.
- **Filter tasks** — `Owner.get_tasks_for_pet(name)` returns tasks for a single pet; `Owner.get_tasks_by_status(completed)` returns all done or all pending tasks across every pet — useful for a to-do vs. done split in the UI.
- **Recurring tasks** — `Task.mark_complete()` automatically returns a fresh `Task` instance for the next occurrence. Daily tasks recur in 1 day; weekly tasks recur in 7 days (`timedelta`). `as_needed` tasks return `None` — no automatic recurrence.
- **Conflict detection** — `Scheduler.detect_conflicts(schedule)` scans all scheduled items for overlapping time windows using the condition `a.start < b.end AND b.start < a.end`. Returns human-readable warning strings instead of raising exceptions, so the app can display them without crashing.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
