from __future__ import annotations
from pathlib import Path

import logging

from task import Task
from task_queue import TaskQueue
from exceptions import TaskValidationError, TaskPriorityError, TaskPayloadError
from system import GeneratorTaskSource, APITaskSource, FileTaskSource, create_sample_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_queue_basic() -> None:
    """Базовые операции очереди."""

    logger.info("\nQueue basic operations")

    queue = TaskQueue()
    queue.add(Task(payload="Buy groceries", priority=5))
    queue.add(Task(payload="Call mom", priority=2))
    queue.add(Task(payload="Read book", priority=8))
    logger.info(f"Queue after adding tasks: {queue}")

    logger.info("Iterating with for-loop:")
    for i, task in enumerate(queue, 1):
        logger.info(f"  {i}. {task.payload} (priority={task.priority})")

    logger.info(f"Queue length: {len(queue)}")
    logger.info(f"Queue is non-empty: {bool(queue)}")


def demo_queue_filters() -> None:
    """Ленивая фильтрация."""

    logger.info("\nLazy filtering")

    queue = TaskQueue()
    tasks = [
        Task("Task A", 3),
        Task("Task B", 7),
        Task("Task C", 1),
        Task("Task D", 5),
        Task("Task E", 9),
    ]
    queue.extend(tasks)

    for t in queue:
        if t.payload == "Task A":
            t._mark_ready()

    logger.info("Filter by status 'new':")
    for t in queue.filter_by_status("new"):
        logger.info(f"  {t.payload} (status={t.status})")

    logger.info("Filter by priority range [1, 5]:")
    for t in queue.filter_by_priority(1, 5):
        logger.info(f"  {t.payload} (priority={t.priority})")


def demo_queue_iteration() -> None:
    """Повторный обход и совместимость."""

    logger.info("\nRepeated iteration")

    queue = TaskQueue()
    queue.extend([Task("Alpha", 3), Task("Beta", 7), Task("Gamma", 1)])

    first_pass = list(queue)
    second_pass = list(queue)
    logger.info(f"First pass count: {len(first_pass)}")
    logger.info(f"Second pass count: {len(second_pass)}")
    logger.info(f"Repeated iteration works: {first_pass == second_pass}")

    total_priority = sum(t.priority for t in queue)
    logger.info(f"Sum of priorities: {total_priority}")


def demo_queue_pop() -> None:
    """Извлечение задач (FIFO)."""

    logger.info("\nPop operations (FIFO)")

    queue = TaskQueue()
    queue.extend([Task("First", 1), Task("Second", 2), Task("Third", 3)])
    logger.info(f"Queue before pop: {queue}")

    popped = queue.pop()
    logger.info(f"Popped: {popped.payload}")
    logger.info(f"Queue after pop: {queue}")

    logger.info("Trying to pop from empty queue:")
    queue.clear()
    try:
        queue.pop()
    except TaskValidationError as e:
        logger.error(f"  {e}")


def demo_queue_validation() -> None:
    """Валидация типов."""

    logger.info("\nValidation")

    queue = TaskQueue()
    try:
        queue.add("not a task")  # type: ignore
    except TaskValidationError as e:
        logger.error(f"  {e}")

    try:
        queue.extend([Task("Valid", 5), "invalid"])  # type: ignore
    except TaskValidationError as e:
        logger.error(f"  {e}")


def demo_queue_sources() -> None:
    """Загрузка из источников."""

    logger.info("\nLoading from sources")

    gen_source = GeneratorTaskSource(count=2, prefix="gen")
    queue = TaskQueue()
    queue.extend(gen_source.get_tasks())
    logger.info(f"Loaded from GeneratorTaskSource: {queue}")

    api_source = APITaskSource()
    queue2 = TaskQueue()
    queue2.extend(api_source.get_tasks())
    logger.info(f"Loaded from APITaskSource: {queue2}")

    test_file = Path("demo_tasks_lab3.json")
    create_sample_file(test_file, [
        {"payload": "File task", "priority": 5},
    ])
    file_source = FileTaskSource(test_file)
    queue3 = TaskQueue()
    queue3.extend(file_source.get_tasks())
    logger.info(f"Loaded from FileTaskSource: {queue3}")
    test_file.unlink()


def main() -> None:

    try:
        logger.info("TaskQueue demonstration started.")

        demo_queue_basic()
        demo_queue_filters()
        demo_queue_iteration()
        demo_queue_pop()
        demo_queue_validation()
        demo_queue_sources()

        logger.info("Demonstration completed.")

    except TaskValidationError as e:
        logger.error(f"Validation error: {e}")
        raise
    except TaskPriorityError as e:
        logger.error(f"Priority error: {e}")
        raise
    except TaskPayloadError as e:
        logger.error(f"Payload error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
