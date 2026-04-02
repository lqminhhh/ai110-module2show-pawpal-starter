from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------------------
# Priority
# ---------------------------------------------------------------------------

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    name: str
    available_minutes: int = 120

    def to_dict(self) -> dict:
        pass

    @classmethod
    def from_dict(cls, data: dict) -> Owner:
        pass


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str  # "dog", "cat", or "other"

    def to_dict(self) -> dict:
        pass

    @classmethod
    def from_dict(cls, data: dict) -> Pet:
        pass


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def is_valid(self) -> bool:
        pass

    def to_dict(self) -> dict:
        pass

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        pass


# ---------------------------------------------------------------------------
# ScheduledItem
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
        pass

    def end_time_str(self) -> str:
        pass

    def to_dict(self) -> dict:
        pass


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------

class Schedule:
    def __init__(
        self,
        owner: Owner,
        pet: Pet,
        items: list[ScheduledItem],
        skipped_tasks: list[Task],
        date_label: str = "Today",
    ):
        self.owner = owner
        self.pet = pet
        self.items = items
        self.skipped_tasks = skipped_tasks
        self.date_label = date_label
        self.total_minutes_scheduled = sum(item.task.duration_minutes for item in items)

    def summary(self) -> str:
        pass

    def to_table_data(self) -> list[dict]:
        pass

    def skipped_summary(self) -> str:
        pass


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------

class Planner:
    def __init__(
        self,
        owner: Owner,
        pet: Pet,
        tasks: list[Task] | None = None,
        day_start_minute: int = 480,  # 8:00 AM
    ):
        self.owner = owner
        self.pet = pet
        self.tasks: list[Task] = tasks or []
        self.day_start_minute = day_start_minute

    def set_tasks(self, tasks: list[Task]) -> None:
        pass

    def _sort_tasks(self) -> list[Task]:
        pass

    def generate(self) -> Schedule:
        pass
