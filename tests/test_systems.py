from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import types
import pytest

from src.task import Task
from src.task_queue import TaskQueue
from src.exceptions import TaskValidationError


class TestTaskQueueCreation:
    """Тесты создания очереди."""

    def test_empty_queue(self):
        q = TaskQueue()
        assert len(q) == 0
        assert not q  # __bool__

    def test_queue_repr(self):
        q = TaskQueue()
        assert repr(q) == "TaskQueue(tasks=0)"

        q.add(Task("Test", 5))
        assert repr(q) == "TaskQueue(tasks=1)"


class TestTaskQueueAdd:
    """Тесты добавления задач."""

    def test_add_single_task(self):
        q = TaskQueue()
        task = Task("A", 5)
        q.add(task)
        assert len(q) == 1

    def test_add_multiple_tasks(self):
        q = TaskQueue()
        q.add(Task("A", 1))
        q.add(Task("B", 2))
        q.add(Task("C", 3))
        assert len(q) == 3

    def test_add_invalid_type_raises_error(self):
        q = TaskQueue()
        with pytest.raises(TaskValidationError, match="Expected Task"):
            q.add("not a task")  # type: ignore

    def test_add_int_raises_error(self):
        q = TaskQueue()
        with pytest.raises(TaskValidationError):
            q.add(123)  # type: ignore


class TestTaskQueueExtend:
    """Тесты批量 добавления."""

    def test_extend_with_list(self):
        q = TaskQueue()
        tasks = [Task("A", 1), Task("B", 2), Task("C", 3)]
        q.extend(tasks)
        assert len(q) == 3

    def test_extend_with_generator(self):
        q = TaskQueue()
        def gen():
            for i in range(5):
                yield Task(f"Task-{i}", i + 1)
        q.extend(gen())
        assert len(q) == 5

    def test_extend_with_empty_iterable(self):
        q = TaskQueue()
        q.extend([])
        assert len(q) == 0

    def test_extend_with_invalid_item_raises_error(self):
        q = TaskQueue()
        with pytest.raises(TaskValidationError):
            q.extend([Task("A", 1), "bad", Task("B", 2)])  # type: ignore


class TestTaskQueueIteration:
    """Тесты итерации и повторного обхода."""

    def test_for_loop(self):
        q = TaskQueue()
        q.extend([Task("A", 1), Task("B", 2), Task("C", 3)])
        payloads = [t.payload for t in q]
        assert payloads == ["A", "B", "C"]

    def test_list_conversion(self):
        q = TaskQueue()
        q.extend([Task("A", 1), Task("B", 2)])
        tasks_list = list(q)
        assert len(tasks_list) == 2

    def test_repeated_iteration(self):
        q = TaskQueue()
        q.extend([Task("A", 1), Task("B", 2)])
        first = list(q)
        second = list(q)
        assert first == second  # повторный обход работает

    def test_nested_loops(self):
        q = TaskQueue()
        q.extend([Task("A", 1), Task("B", 2)])
        count = 0
        for t1 in q:
            for t2 in q:
                count += 1
        assert count == 4  # 2 * 2

    def test_iterator_independence(self):
        q = TaskQueue()
        q.extend([Task("A", 1), Task("B", 2)])
        it1 = iter(q)
        it2 = iter(q)
        assert it1 is not it2  # разные итераторы


class TestTaskQueueFilters:
    """Тесты ленивых фильтров."""

    @pytest.fixture
    def queue(self):
        q = TaskQueue()
        tasks = [
            Task("New-1", 3),
            Task("New-2", 7),
            Task("Ready-1", 5),
            Task("Done-1", 1),
            Task("Cancelled-1", 10),
        ]
        q.extend(tasks)
        # Изменим статусы некоторых
        for t in q:
            if "Ready" in t.payload:
                t._mark_ready()
            elif "Done" in t.payload:
                t._mark_done()
            elif "Cancelled" in t.payload:
                t._mark_cancelled()
        return q

    def test_filter_by_status_returns_generator(self, queue):
        gen = queue.filter_by_status("new")
        assert isinstance(gen, types.GeneratorType)

    def test_filter_by_status_new(self, queue):
        new_tasks = list(queue.filter_by_status("new"))
        assert len(new_tasks) == 2

    def test_filter_by_status_ready(self, queue):
        ready_tasks = list(queue.filter_by_status("ready"))
        assert len(ready_tasks) == 1
        assert "Ready" in ready_tasks[0].payload

    def test_filter_by_status_done(self, queue):
        done_tasks = list(queue.filter_by_status("done"))
        assert len(done_tasks) == 1

    def test_filter_by_status_no_match(self, queue):
        processing = list(queue.filter_by_status("processing"))
        assert len(processing) == 0

    def test_filter_by_priority_returns_generator(self, queue):
        gen = queue.filter_by_priority(1, 5)
        assert isinstance(gen, types.GeneratorType)

    def test_filter_by_priority_range(self, queue):
        low = list(queue.filter_by_priority(1, 5))
        assert all(1 <= t.priority <= 5 for t in low)

    def test_filter_by_priority_single(self, queue):
        exact = list(queue.filter_by_priority(7, 7))
        assert len(exact) == 1
        assert exact[0].priority == 7

    def test_filter_by_priority_full_range(self, queue):
        all_tasks = list(queue.filter_by_priority(1, 10))
        assert len(all_tasks) == 5

    def test_filter_active(self, queue):
        active = list(queue.filter_active())
        # is_active проверяет status not in {"completed", "cancelled"}
        # "done" считается активным (т.к. нет статуса "completed")
        # только "cancelled" — не активен
        assert len(active) == 4

    def test_filter_active_excludes_cancelled(self, queue):
        active = list(queue.filter_active())
        for t in active:
            assert t.status != "cancelled"

    def test_stream_returns_generator(self, queue):
        gen = queue.stream()
        assert isinstance(gen, types.GeneratorType)

    def test_stream_yields_all_tasks(self, queue):
        streamed = list(queue.stream())
        assert len(streamed) == 5


class TestTaskQueuePop:
    """Тесты извлечения задач."""

    def test_pop_returns_first_task(self):
        q = TaskQueue()
        t1 = Task("First", 1)
        t2 = Task("Second", 2)
        q.extend([t1, t2])
        assert q.pop() is t1

    def test_pop_reduces_length(self):
        q = TaskQueue()
        q.extend([Task("A", 1), Task("B", 2)])
        q.pop()
        assert len(q) == 1

    def test_pop_empty_raises_error(self):
        q = TaskQueue()
        with pytest.raises(TaskValidationError, match="Queue is empty"):
            q.pop()

    def test_fifo_order(self):
        q = TaskQueue()
        tasks = [Task(f"T-{i}", i + 1) for i in range(3)]  # priority 1,2,3
        q.extend(tasks)
        assert q.pop() is tasks[0]
        assert q.pop() is tasks[1]
        assert q.pop() is tasks[2]


class TestTaskQueueClear:
    """Тесты очистки очереди."""

    def test_clear_empties_queue(self):
        q = TaskQueue()
        q.extend([Task("A", 1), Task("B", 2)])
        q.clear()
        assert len(q) == 0
        assert not q

    def test_clear_then_add(self):
        q = TaskQueue()
        q.extend([Task("A", 1)])
        q.clear()
        q.add(Task("B", 2))
        assert len(q) == 1


class TestTaskQueueMagicMethods:
    """Тесты специальных методов."""

    def test_len(self):
        q = TaskQueue()
        assert len(q) == 0
        q.add(Task("A", 1))
        assert len(q) == 1

    def test_bool_empty(self):
        q = TaskQueue()
        assert bool(q) is False

    def test_bool_nonempty(self):
        q = TaskQueue()
        q.add(Task("A", 1))
        assert bool(q) is True

    def test_contains_true(self):
        q = TaskQueue()
        t = Task("A", 1)
        q.add(t)
        assert t in q

    def test_contains_false(self):
        q = TaskQueue()
        t = Task("A", 1)
        assert t not in q

    def test_sum_priorities(self):
        q = TaskQueue()
        q.extend([Task("A", 3), Task("B", 7), Task("C", 1)])
        assert sum(t.priority for t in q) == 11


class TestTaskQueueCompatibility:
    """Тесты совместимости со стандартными конструкциями."""

    def test_list_comprehension(self):
        q = TaskQueue()
        q.extend([Task("A", 1), Task("B", 2), Task("C", 3)])
        priorities = [t.priority for t in q]
        assert priorities == [1, 2, 3]

    def test_filter_builtin(self):
        q = TaskQueue()
        q.extend([Task("A", 1), Task("B", 10), Task("C", 5)])
        high = list(filter(lambda t: t.priority > 5, q))
        assert len(high) == 1

    def test_sorted_by_priority(self):
        q = TaskQueue()
        q.extend([Task("A", 7), Task("B", 1), Task("C", 5)])
        sorted_tasks = sorted(q, key=lambda t: t.priority)
        assert sorted_tasks[0].priority == 1
        assert sorted_tasks[-1].priority == 7

    def test_max_min_priority(self):
        q = TaskQueue()
        q.extend([Task("A", 7), Task("B", 1), Task("C", 5)])
        assert max(q, key=lambda t: t.priority).priority == 7
        assert min(q, key=lambda t: t.priority).priority == 1
