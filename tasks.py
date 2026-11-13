"""A tiny task store backed by a JSON file.

Standard library only, so it runs anywhere Python 3.10+ does, including
inside a Docker Sandbox with nothing extra installed.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

MAX_TITLE_LENGTH = 200


def default_path() -> Path:
    return Path(os.environ.get("TASKS_FILE", "data/tasks.json"))


@dataclass
class Task:
    id: str
    title: str
    done: bool = False
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class TaskStore:
    """Reads and writes tasks to a JSON file. Built for a single process."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else default_path()
        self._lock = threading.Lock()

    def _load(self) -> list[Task]:
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as f:
            raw = json.load(f)
        return [Task(**item) for item in raw]

    def _save(self, tasks: list[Task]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump([t.to_dict() for t in tasks], f, indent=2)
        tmp.replace(self.path)

    def list_tasks(self) -> list[Task]:
        """Open tasks first, newest first within each group."""
        with self._lock:
            tasks = self._load()
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        tasks.sort(key=lambda t: t.done)
        return tasks

    def add(self, title: str) -> Task:
        title = (title or "").strip()
        if not title:
            raise ValueError("Title can't be empty.")
        if len(title) > MAX_TITLE_LENGTH:
            raise ValueError(f"Title must be {MAX_TITLE_LENGTH} characters or fewer.")
        task = Task(
            id=uuid.uuid4().hex[:8],
            title=title,
            created_at=datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        )
        with self._lock:
            tasks = self._load()
            tasks.append(task)
            self._save(tasks)
        return task

    def toggle(self, task_id: str) -> Task:
        with self._lock:
            tasks = self._load()
            for task in tasks:
                if task.id == task_id:
                    task.done = not task.done
                    self._save(tasks)
                    return task
        raise KeyError(task_id)

    def delete(self, task_id: str) -> None:
        with self._lock:
            tasks = self._load()
            remaining = [t for t in tasks if t.id != task_id]
            if len(remaining) == len(tasks):
                raise KeyError(task_id)
            self._save(remaining)
