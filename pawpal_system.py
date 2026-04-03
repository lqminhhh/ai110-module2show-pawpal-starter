from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import ClassVar
from datetime import date, timedelta
from enum import Enum


# ---------------------------------------------------------------------------
# Priority
# ---------------------------------------------------------------------------

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


# ---------------------------------------------------------------------------
# Task
# Represents a single care activity with time, frequency, and completion state.
# ---------------------------------------------------------------------------

@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority
    frequency: str = "daily"      # "daily", "weekly", or "as_needed"
    completed: bool = False
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Algorithm 3: frequency-aware due date check
    # Maps each frequency string to the weekday numbers it applies to.
    # daily → every day; weekly → Monday only (0); as_needed → always included.
    _FREQUENCY_DAYS: ClassVar[dict] = {
        "daily": set(range(7)),       # 0=Mon … 6=Sun
        "weekly": {0},                # Mondays only
        "as_needed": set(range(7)),   # always eligible
    }

    def due_today(self, day_of_week: int) -> bool:
        """
        Return True if this task should appear in today's schedule.

        day_of_week follows Python's weekday() convention: 0 = Monday, 6 = Sunday.
        Weekly tasks are only due on Mondays; daily and as_needed tasks are due
        every day.

        Why: without this check the scheduler would include a 'weekly grooming'
        task every single day, which defeats the purpose of the frequency field.
        """
        eligible_days = self._FREQUENCY_DAYS.get(self.frequency, set(range(7)))
        return day_of_week in eligible_days

    def is_valid(self) -> bool:
        """Return True if the task has a non-empty title and positive duration."""
        return bool(self.title.strip()) and self.duration_minutes >= 1

    def mark_complete(self) -> Task | None:
        """
        Mark this task as done and, for recurring tasks, return a fresh Task
        instance representing the next occurrence.

        - daily   → next occurrence is today + 1 day  (uses timedelta(days=1))
        - weekly  → next occurrence is today + 7 days (uses timedelta(days=7))
        - as_needed → no automatic recurrence; returns None

        The caller is responsible for adding the returned Task back to the pet.
        Returning a new object (rather than mutating this one) keeps the
        completed record intact for history/logging purposes.
        """
        self.completed = True

        next_deltas = {"daily": timedelta(days=1), "weekly": timedelta(days=7)}
        delta = next_deltas.get(self.frequency)
        if delta is None:
            return None

        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            completed=False,
        )

    def reset(self) -> None:
        """Clear completion status (e.g. at the start of a new day)."""
        self.completed = False

    def to_dict(self) -> dict:
        """Serialize to a plain dict for st.session_state storage."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority.name,   # store "HIGH", not Priority.HIGH
            "frequency": self.frequency,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Reconstruct a Task from a plain dict."""
        return cls(
            title=data["title"],
            duration_minutes=data["duration_minutes"],
            priority=Priority[data["priority"]],
            frequency=data.get("frequency", "daily"),
            completed=data.get("completed", False),
            task_id=data.get("task_id", str(uuid.uuid4())),
        )


# ---------------------------------------------------------------------------
# Pet
# Stores pet details and owns a list of tasks for that pet.
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str                                      # "dog", "cat", or "other"
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list if it is valid."""
        if not task.is_valid():
            raise ValueError(f"Task '{task.title}' is not valid.")
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task by its ID. Raises KeyError if not found."""
        for i, t in enumerate(self.tasks):
            if t.task_id == task_id:
                self.tasks.pop(i)
                return
        raise KeyError(f"No task with id '{task_id}' found for pet '{self.name}'.")

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that have not yet been completed."""
        return [t for t in self.tasks if not t.completed]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "species": self.species,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Pet:
        return cls(
            name=data["name"],
            species=data["species"],
            tasks=[Task.from_dict(t) for t in data.get("tasks", [])],
        )


# ---------------------------------------------------------------------------
# Owner
# Manages one or more pets and provides a single access point for all tasks.
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    name: str
    available_minutes: int = 120              # total care time per day
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Collect and return every task across all pets in a flat list."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> list[Task]:
        """Return only incomplete tasks across all pets."""
        return [task for pet in self.pets for task in pet.get_pending_tasks()]

    # Algorithm 2a: filter by pet name
    def get_tasks_for_pet(self, pet_name: str) -> list[Task]:
        """
        Return all tasks belonging to the pet with the given name.

        Why: useful for showing a per-pet task list in the UI without
        exposing the internal pets list to every caller.
        Comparison is case-insensitive so 'Mochi' and 'mochi' both work.
        """
        name = pet_name.strip().lower()
        for pet in self.pets:
            if pet.name.lower() == name:
                return list(pet.tasks)
        return []

    # Algorithm 2b: filter by completion status across all pets
    def get_tasks_by_status(self, completed: bool) -> list[Task]:
        """
        Return all tasks (across all pets) that match the given completion status.

        get_tasks_by_status(completed=False) → every task still to be done today.
        get_tasks_by_status(completed=True)  → every task already finished today.

        Why: lets the UI show a 'done' checklist separately from the 'to-do' list.
        """
        return [
            task
            for pet in self.pets
            for task in pet.tasks
            if task.completed == completed
        ]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "available_minutes": self.available_minutes,
            "pets": [p.to_dict() for p in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Owner:
        return cls(
            name=data["name"],
            available_minutes=data.get("available_minutes", 120),
            pets=[Pet.from_dict(p) for p in data.get("pets", [])],
        )


# ---------------------------------------------------------------------------
# ScheduledItem
# A Task that has been placed at a concrete time slot in the day.
# ---------------------------------------------------------------------------

@dataclass
class ScheduledItem:
    task: Task
    start_minute: int
    reason: str
    end_minute: int = field(init=False)

    def __post_init__(self):
        self.end_minute = self.start_minute + self.task.duration_minutes

    def start_time_str(self) -> str:
        """Convert start_minute offset to a readable string like '8:00 AM'."""
        hour, minute = divmod(self.start_minute, 60)
        period = "AM" if hour < 12 else "PM"
        hour = hour % 12 or 12
        return f"{hour}:{minute:02d} {period}"

    def end_time_str(self) -> str:
        """Convert end_minute offset to a readable string like '8:30 AM'."""
        hour, minute = divmod(self.end_minute, 60)
        period = "AM" if hour < 12 else "PM"
        hour = hour % 12 or 12
        return f"{hour}:{minute:02d} {period}"

    def to_dict(self) -> dict:
        """Flat dict suitable for st.table() / st.dataframe()."""
        return {
            "Task": self.task.title,
            "Priority": self.task.priority.name.capitalize(),
            "Duration (min)": self.task.duration_minutes,
            "Start": self.start_time_str(),
            "End": self.end_time_str(),
            "Reason": self.reason,
        }


# ---------------------------------------------------------------------------
# Schedule
# The output of a Scheduler run: ordered items + skipped tasks + explanations.
# ---------------------------------------------------------------------------

class Schedule:
    def __init__(
        self,
        owner: Owner,
        items: list[ScheduledItem],
        skipped_tasks: list[Task],
        date_label: str = "Today",
    ):
        self.owner = owner
        self.items = items
        self.skipped_tasks = skipped_tasks
        self.date_label = date_label
        self.total_minutes_scheduled = sum(item.task.duration_minutes for item in items)

    def summary(self) -> str:
        """Return a human-readable overview of the plan."""
        lines = [
            f"**{self.date_label}'s plan for {self.owner.name}**",
            f"- {len(self.items)} task(s) scheduled across "
            f"{len(self.owner.pets)} pet(s)",
            f"- Total time: {self.total_minutes_scheduled} min "
            f"(of {self.owner.available_minutes} min available)",
        ]
        if self.skipped_tasks:
            lines.append(f"- {len(self.skipped_tasks)} task(s) skipped (not enough time)")
        return "\n".join(lines)

    def to_table_data(self) -> list[dict]:
        """Return a list of flat dicts, one per scheduled item, for st.table()."""
        return [item.to_dict() for item in self.items]

    def skipped_summary(self) -> str:
        """Return a sentence describing skipped tasks, or empty string if none."""
        if not self.skipped_tasks:
            return ""
        names = ", ".join(t.title for t in self.skipped_tasks)
        return f"Skipped (time ran out): {names}."


# ---------------------------------------------------------------------------
# Scheduler
# The "brain" — retrieves all tasks from the Owner's pets, organizes them by
# priority, and fits them into the owner's available time for the day.
#
# How it retrieves tasks:
#   Owner.get_all_pending_tasks() iterates over every pet's task list and
#   returns a flat list.  Scheduler calls that one method so it never needs
#   to know about Pet internals directly.
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner, day_start_minute: int = 480):
        self.owner = owner
        self.day_start_minute = day_start_minute  # default 8:00 AM

    def get_all_tasks(self) -> list[Task]:
        """
        Retrieve every pending (incomplete) task across all of the owner's pets.

        Delegates to Owner.get_all_pending_tasks() so the Scheduler never
        reaches into Pet directly — Owner is the single access point.
        """
        return self.owner.get_all_pending_tasks()

    def _prioritize(self, tasks: list[Task]) -> list[Task]:
        """
        Sort tasks so the most urgent work comes first.
        Tiebreaker: shorter tasks go before longer ones at the same priority
        (complete more items when time is tight).
        """
        return sorted(tasks, key=lambda t: (-t.priority.value, t.duration_minutes))

    def generate(self, day_of_week: int | None = None) -> Schedule:
        """
        Build a daily Schedule using a greedy algorithm:
        1. Retrieve all pending tasks via get_all_tasks().
        2. Algorithm 3 — filter out tasks not due today using due_today().
        3. Sort them by priority (high → low), then duration (short → long).
        4. Walk the sorted list; fit each task that still has room in the
           available time window; skip the rest.
        5. Algorithm 1 — sort output items by start_minute so the table
           always reads in chronological order.
        6. Return a Schedule with scheduled items and skipped tasks.

        day_of_week: 0=Monday … 6=Sunday. Defaults to today via date.today().
        """
        if day_of_week is None:
            day_of_week = date.today().weekday()

        # Algorithm 3: drop tasks whose frequency says they aren't due today
        all_tasks = [t for t in self.get_all_tasks() if t.due_today(day_of_week)]

        sorted_tasks = self._prioritize(all_tasks)

        items: list[ScheduledItem] = []
        skipped: list[Task] = []
        current_minute = self.day_start_minute
        remaining = self.owner.available_minutes

        for task in sorted_tasks:
            if task.duration_minutes <= remaining:
                reason = (
                    f"{task.priority.name.capitalize()} priority task scheduled "
                    f"at {self._minute_to_time(current_minute)}."
                )
                items.append(ScheduledItem(task, current_minute, reason))
                current_minute += task.duration_minutes
                remaining -= task.duration_minutes
            else:
                skipped.append(task)

        # Algorithm 1: sort scheduled items by start time for clean display
        items.sort(key=lambda i: i.start_minute)

        return Schedule(self.owner, items, skipped)

    def sort_by_time(self, items: list[ScheduledItem]) -> list[ScheduledItem]:
        """Sort ScheduledItems into chronological order by start time.

        Uses ``sorted()`` with a lambda key on ``start_minute`` (an integer
        offset from midnight).  Sorting an integer is equivalent to sorting
        "HH:MM" strings but requires no string parsing or conversion.

        Args:
            items: A list of ScheduledItem objects in any order.

        Returns:
            A new list of the same ScheduledItems sorted earliest-first.
            The original list is not mutated.

        Example::

            sorted_items = scheduler.sort_by_time(schedule.items)
        """
        return sorted(items, key=lambda item: item.start_minute)

    def detect_conflicts(self, schedule: Schedule) -> list[str]:
        """Scan a Schedule for overlapping time windows and return warning messages.

        Two scheduled items conflict when their windows overlap, defined by:
            ``a.start_minute < b.end_minute  AND  b.start_minute < a.end_minute``

        This covers both partial overlaps (one task starts inside another) and
        exact-same-start conflicts.

        Lightweight strategy: returns human-readable warning strings rather than
        raising exceptions, so the caller can display them without crashing the app.

        Args:
            schedule: The Schedule object whose ``items`` list will be scanned.

        Returns:
            A list of warning strings, one per conflicting pair.
            Returns an empty list if the schedule is conflict-free.

        Complexity:
            O(n²) pairwise comparison — acceptable for the small number of
            daily care tasks a pet owner would have (typically fewer than 20).

        Example::

            warnings = scheduler.detect_conflicts(schedule)
            for w in warnings:
                print(w)
        """
        warnings = []
        for i, a in enumerate(schedule.items):
            for b in schedule.items[i + 1:]:
                if a.start_minute < b.end_minute and b.start_minute < a.end_minute:
                    warnings.append(
                        f"WARNING: '{a.task.title}' ({a.start_time_str()}–{a.end_time_str()}) "
                        f"overlaps with '{b.task.title}' ({b.start_time_str()}–{b.end_time_str()})"
                    )
        return warnings

    @staticmethod
    def _minute_to_time(minute: int) -> str:
        hour, min_ = divmod(minute, 60)
        period = "AM" if hour < 12 else "PM"
        hour = hour % 12 or 12
        return f"{hour}:{min_:02d} {period}"
