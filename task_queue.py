from __future__ import annotations
from task import Task
from typing import runtime_checkable, Protocol, Any
from collections.abc import Iterable, Iterator, Generator
from system import TaskSource


class TaskQueue:
    def __init__(self) -> None:
        self._tasks: list[Task] = []
    
    def __iter__(self) -> Iterator[Task]:
        return iter(self._tasks)
    
    def add(self, task: Task) -> None:
        self._tasks.append(task)

    def extend(self, tasks: Iterable[Task]) -> None:
        self._tasks.extend(tasks)

    def filter_by_status(self, status: str) -> Generator[Task, None, None]:
        for task in self._tasks:
            if task.status == status:
                yield task
        
    def filter_by_priority(self, priority: int, min_p: int, max_p: int = 10) -> Generator[Task, None, None]:
        for task in self._tasks:
            if task.priority == priority:
                yield task
    
    def filter_active(self) -> Generator[Task, None, None]:
        for task in self._tasks:
            if task.is_active:
                yield task

    def stream(self) -> Generator[Task, None, None]:
        yield from self._tasks
    
    def __len__(self) -> int:
        return len(self._tasks)
    def __bool__(self) -> bool:
        return bool(self._tasks)
    def __contains__(self, task: Task) -> bool:
        return task in self._tasks
    def __repr__(self) -> str:
        return f"TaskQueue(tasks={len(self._tasks)})"
    
    def load_from(self, source: TaskSource) -> None: # альтернатива extend
        self.extend(source.get_tasks())