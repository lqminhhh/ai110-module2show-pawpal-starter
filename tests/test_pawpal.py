from pawpal_system import Task, Pet, Owner, Priority, Scheduler, ScheduledItem, Schedule


def test_mark_complete_changes_status():
    task = Task(title="Morning walk", duration_minutes=30, priority=Priority.HIGH)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Feeding", duration_minutes=10, priority=Priority.HIGH))
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """Tasks added out of order must come back sorted earliest-first."""
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Grooming",     duration_minutes=15, priority=Priority.LOW,  frequency="daily"))
    pet.add_task(Task(title="Morning walk", duration_minutes=30, priority=Priority.HIGH, frequency="daily"))
    pet.add_task(Task(title="Feeding",      duration_minutes=10, priority=Priority.HIGH, frequency="daily"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    schedule = scheduler.generate(day_of_week=0)

    sorted_items = scheduler.sort_by_time(schedule.items)
    start_minutes = [item.start_minute for item in sorted_items]
    assert start_minutes == sorted(start_minutes), (
        "sort_by_time() should return items in ascending start_minute order"
    )


def test_sort_by_time_does_not_mutate_original():
    """sort_by_time() must return a new list and leave the original unchanged."""
    owner = Owner(name="Jordan", available_minutes=60)
    pet = Pet(name="Luna", species="cat")
    pet.add_task(Task(title="Playtime", duration_minutes=20, priority=Priority.MEDIUM, frequency="daily"))
    pet.add_task(Task(title="Feeding",  duration_minutes=10, priority=Priority.HIGH,   frequency="daily"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    schedule = scheduler.generate(day_of_week=0)
    original_order = [item.task.title for item in schedule.items]

    scheduler.sort_by_time(schedule.items)   # call but discard result

    assert [item.task.title for item in schedule.items] == original_order, (
        "sort_by_time() must not modify the original list in place"
    )


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_daily_task_mark_complete_creates_next_occurrence():
    """mark_complete() on a daily task must return a fresh, incomplete Task."""
    task = Task(title="Morning walk", duration_minutes=30,
                priority=Priority.HIGH, frequency="daily")
    next_task = task.mark_complete()

    assert task.completed is True, "Original task should be marked complete"
    assert next_task is not None, "Daily task should produce a next occurrence"
    assert next_task.completed is False, "Next occurrence must start incomplete"
    assert next_task.title == task.title, "Next occurrence should have the same title"
    assert next_task.frequency == "daily", "Next occurrence should keep the same frequency"


def test_weekly_task_mark_complete_creates_next_occurrence():
    """mark_complete() on a weekly task must also return a next occurrence."""
    task = Task(title="Grooming", duration_minutes=15,
                priority=Priority.LOW, frequency="weekly")
    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.completed is False
    assert next_task.frequency == "weekly"


def test_as_needed_task_mark_complete_returns_none():
    """mark_complete() on an as_needed task must return None (no recurrence)."""
    task = Task(title="Special treat", duration_minutes=5,
                priority=Priority.LOW, frequency="as_needed")
    next_task = task.mark_complete()

    assert next_task is None, "as_needed tasks should not auto-create a next occurrence"


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def _make_schedule(owner: Owner, items: list) -> Schedule:
    """Helper: wrap a list of ScheduledItems in a Schedule."""
    return Schedule(owner=owner, items=items, skipped_tasks=[])


def test_detect_conflicts_flags_overlapping_tasks():
    """Two tasks occupying the same time window must trigger a warning."""
    owner = Owner(name="Jordan", available_minutes=120)

    task_a = Task(title="Bath time", duration_minutes=20, priority=Priority.MEDIUM)
    task_b = Task(title="Nail trim", duration_minutes=15, priority=Priority.LOW)

    # task_b starts at minute 550, inside task_a's window (540–560)
    items = [
        ScheduledItem(task=task_a, start_minute=540, reason="test"),
        ScheduledItem(task=task_b, start_minute=550, reason="test"),
    ]
    schedule = _make_schedule(owner, items)

    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts(schedule)

    assert len(warnings) == 1, "Exactly one overlapping pair should be detected"
    assert "Bath time" in warnings[0]
    assert "Nail trim" in warnings[0]


def test_detect_conflicts_no_warning_for_sequential_tasks():
    """Tasks placed back-to-back (no gap, no overlap) must not trigger a warning."""
    owner = Owner(name="Jordan", available_minutes=120)

    task_a = Task(title="Feeding",      duration_minutes=10, priority=Priority.HIGH)
    task_b = Task(title="Morning walk", duration_minutes=30, priority=Priority.HIGH)

    # task_b starts exactly when task_a ends — not an overlap
    items = [
        ScheduledItem(task=task_a, start_minute=480, reason="test"),  # 8:00–8:10
        ScheduledItem(task=task_b, start_minute=490, reason="test"),  # 8:10–8:40
    ]
    schedule = _make_schedule(owner, items)

    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts(schedule)

    assert warnings == [], "Back-to-back tasks must not be flagged as conflicting"


def test_detect_conflicts_exact_same_start_time():
    """Two tasks that start at the identical minute must be flagged."""
    owner = Owner(name="Jordan", available_minutes=120)

    task_a = Task(title="Playtime",  duration_minutes=20, priority=Priority.MEDIUM)
    task_b = Task(title="Grooming",  duration_minutes=15, priority=Priority.LOW)

    items = [
        ScheduledItem(task=task_a, start_minute=600, reason="test"),
        ScheduledItem(task=task_b, start_minute=600, reason="test"),
    ]
    schedule = _make_schedule(owner, items)

    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts(schedule)

    assert len(warnings) == 1
    assert "Playtime" in warnings[0]
    assert "Grooming" in warnings[0]
