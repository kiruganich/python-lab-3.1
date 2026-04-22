from __future__ import annotations
from task import Task
from collections.abc import Iterable, Iterator, Generator
from collections import deque
from system import TaskSource
from exceptions import TaskValidationError

import logging
logger = logging.getLogger(__name__)


class TaskQueue:
    """
    Коллекция задач с поддержкой ленивой обработки.

    Совместима со стандартными конструкциями Python: for, list, sum, len, in.
    Поддерживает повторный обход очереди.

    """
    def __init__(self, source: TaskSource | None = None) -> None:
        self._source = source
        self._tasks: deque[Task] = deque()
        if source:
            for task in source.get_tasks():
                self._tasks.append(task)
    
    def __iter__(self) -> Iterator[Task]:
        return iter(self._tasks)
    
    def add(self, task: Task) -> None:
        if not isinstance(task, Task):
            logger.error(f"Expected Task, got {type(task).__name__}")
            raise TaskValidationError(f"Task Validation failed: Expected Task, got {type(task).__name__}")
        self._tasks.append(task)
        logger.debug(f"Task added: {task.id[:8]}... priority={task.priority}")

    def extend(self, tasks: Iterable[Task]) -> None:
        for task in tasks:
            self.add(task)

    def filter_by_status(self, status: str) -> Generator[Task, None, None]:
        for task in self._tasks:
            if task.status == status:
                yield task
        
    def filter_by_priority(self, min_p: int, max_p: int = 10) -> Generator[Task, None, None]:
        for task in self._tasks:
            if min_p <= task.priority <= max_p:
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
    
    def pop(self) -> Task:
        if not self._tasks:
            logger.error("Queue is empty")
            raise TaskValidationError("Task Validation failed: Queue is empty")
        return self._tasks.popleft()
    
    def clear(self) -> None:
        self._tasks = []
        logger.info("Queue cleared")