from pawpal_system import Owner, Pet, Task, Priority, Scheduler, ScheduledItem

# ---------------------------------------------------------------------------
# Setup: tasks added OUT OF ORDER (low priority first, high priority last)
# sort_by_time() and _prioritize() must reorder them correctly.
# ---------------------------------------------------------------------------
owner = Owner(name="Jordan", available_minutes=120)

mochi = Pet(name="Mochi", species="dog")
luna  = Pet(name="Luna",  species="cat")

# Added in reverse-priority order on purpose
mochi.add_task(Task(title="Grooming",      duration_minutes=15, priority=Priority.LOW,    frequency="weekly"))
mochi.add_task(Task(title="Morning walk",  duration_minutes=30, priority=Priority.HIGH,   frequency="daily"))
mochi.add_task(Task(title="Feeding",       duration_minutes=10, priority=Priority.HIGH,   frequency="daily"))
luna.add_task( Task(title="Playtime",      duration_minutes=20, priority=Priority.MEDIUM, frequency="daily"))
luna.add_task( Task(title="Vet meds",      duration_minutes=5,  priority=Priority.HIGH,   frequency="daily"))

owner.add_pet(mochi)
owner.add_pet(luna)

scheduler = Scheduler(owner)

# ---------------------------------------------------------------------------
# 1. Generate schedule (Monday so weekly Grooming IS included)
# ---------------------------------------------------------------------------
schedule = scheduler.generate(day_of_week=0)   # 0 = Monday

print("=" * 58)
print("          TODAY'S SCHEDULE  (Monday)")
print("=" * 58)
print(schedule.summary())
print()

# sort_by_time() re-sorts the already-generated items — demonstrates the method
sorted_items = scheduler.sort_by_time(schedule.items)
print(f"{'Task':<18} {'Priority':<10} {'Freq':<10}  {'Time'}")
print("-" * 58)
for item in sorted_items:
    time_range = f"{item.start_time_str()} – {item.end_time_str()}"
    print(f"{item.task.title:<18} {item.task.priority.name:<10} {item.task.frequency:<10}  {time_range}")

# ---------------------------------------------------------------------------
# 2. Recurring task: mark_complete() returns next-occurrence Task
# ---------------------------------------------------------------------------
print()
print("--- Recurring task demo ---")
walk = mochi.tasks[1]   # Morning walk (daily)
next_task = walk.mark_complete()
if next_task:
    mochi.add_task(next_task)
    print(f"'{walk.title}' marked complete.")
    print(f"Next occurrence auto-created: '{next_task.title}' (completed={next_task.completed})")

# as_needed task returns None
as_needed = Task(title="Special treat", duration_minutes=5,
                 priority=Priority.LOW, frequency="as_needed")
result = as_needed.mark_complete()
print(f"'as_needed' task after mark_complete → next_task={result}  (expected None)")

# ---------------------------------------------------------------------------
# 3. Conflict detection — inject two overlapping items manually
# ---------------------------------------------------------------------------
print()
print("--- Conflict detection demo ---")

task_a = Task(title="Bath time",   duration_minutes=20, priority=Priority.MEDIUM)
task_b = Task(title="Nail trim",   duration_minutes=15, priority=Priority.LOW)

# Force both to start at 9:00 AM (minute 540) so they overlap
conflicting_items = [
    ScheduledItem(task=task_a, start_minute=540, reason="manual"),
    ScheduledItem(task=task_b, start_minute=545, reason="manual"),   # starts inside Bath time
]
schedule.items.extend(conflicting_items)

warnings = scheduler.detect_conflicts(schedule)
if warnings:
    for w in warnings:
        print(w)
else:
    print("No conflicts detected.")

print("=" * 58)
