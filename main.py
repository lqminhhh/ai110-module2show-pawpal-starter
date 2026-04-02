from pawpal_system import Owner, Pet, Task, Priority, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=90)

mochi = Pet(name="Mochi", species="dog")
luna = Pet(name="Luna", species="cat")

# --- Tasks for Mochi (dog) ---
mochi.add_task(Task(title="Morning walk", duration_minutes=30, priority=Priority.HIGH))
mochi.add_task(Task(title="Feeding", duration_minutes=10, priority=Priority.HIGH, frequency="daily"))

# --- Tasks for Luna (cat) ---
luna.add_task(Task(title="Playtime", duration_minutes=20, priority=Priority.MEDIUM))
luna.add_task(Task(title="Grooming", duration_minutes=15, priority=Priority.LOW, frequency="weekly"))

# --- Register pets with owner ---
owner.add_pet(mochi)
owner.add_pet(luna)

# --- Generate schedule ---
scheduler = Scheduler(owner)
schedule = scheduler.generate()

# --- Print results ---
print("=" * 50)
print("        TODAY'S SCHEDULE")
print("=" * 50)
print(schedule.summary())
print()

if schedule.items:
    print(f"{'Task':<20} {'Priority':<10} {'Duration':>8}   {'Time'}")
    print("-" * 50)
    for item in schedule.items:
        time_range = f"{item.start_time_str()} – {item.end_time_str()}"
        print(f"{item.task.title:<20} {item.task.priority.name:<10} {item.task.duration_minutes:>6} min   {time_range}")

if schedule.skipped_tasks:
    print()
    print(schedule.skipped_summary())

print("=" * 50)
