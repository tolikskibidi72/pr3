# завдання 3.2. паттерни Observer, Strategy та архітектурний шаблон MVC

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable


# --- observer ---

class EventEmitter:
    #базовий клас для системи подій (observer)
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}

    def on(self, event: str, callback: Callable):
        #підписка на подію
        self._listeners.setdefault(event, []).append(callback)

    def off(self, event: str, callback: Callable):
        #відписка від події
        if event in self._listeners and callback in self._listeners[event]:
            self._listeners[event].remove(callback)

    def emit(self, event: str, *args, **kwargs):
        #сповіщення всіх слухачів події
        for callback in self._listeners.get(event, []):
            callback(*args, **kwargs)


# --- strategy ---

class SortStrategy(ABC):
    @abstractmethod
    def sort(self, tasks: list["Task"]) -> list["Task"]:
        pass


class SortByPriority(SortStrategy):
    # сортування за пріоритетом (1 - найвищий, 5 - найнижчий)
    def sort(self, tasks: list["Task"]) -> list["Task"]:
        return sorted(tasks, key=lambda t: t.priority)


class SortByDeadline(SortStrategy):
    #сортування за дедлайном (найближчий першим)
    def sort(self, tasks: list["Task"]) -> list["Task"]:
        return sorted(tasks, key=lambda t: t.deadline)


class SortByCreationDate(SortStrategy):
    #Сортування за датою створення (найновіші першими)
    def sort(self, tasks: list["Task"]) -> list["Task"]:
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)


# --- model ---

@dataclass
class Task:
    title: str
    priority: int  # 1 (найвищий) - 5 (найнижчий)
    deadline: datetime
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)


class TaskModel(EventEmitter):
    #модель: зберігання завдань та бізнес-логіка
    def __init__(self):
        super().__init__()
        self._tasks: list[Task] = []

    def add_task(self, title: str, priority: int, deadline: datetime):
        task = Task(title=title, priority=priority, deadline=deadline)
        self._tasks.append(task)
        self.emit("task_added", task)

    def complete_task(self, index: int):
        if 0 <= index < len(self._tasks):
            task = self._tasks[index]
            task.completed = True
            self.emit("task_completed", task)

    def remove_task(self, index: int):
        if 0 <= index < len(self._tasks):
            task = self._tasks.pop(index)
            self.emit("task_removed", task)

    def get_tasks(self, include_completed: bool = True) -> list[Task]:
        if include_completed:
            return list(self._tasks)
        return [t for t in self._tasks if not t.completed]

    def get_statistics(self) -> dict:
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks if t.completed)
        active = total - completed
        return {"total": total, "completed": completed, "active": active}


# --- view ---

class TaskView:
    #вигляд: відображення таблиці завдань та повідомлень у консолі
    def show_tasks(self, tasks: list[Task], title: str = "завдання"):
        print(f"\n=== {title} ===")
        if not tasks:
            print("  список порожній")
            return

        header = f"{'№':<3} | {'назва':<26} | {'пріор.':<6} | {'дедлайн':<10} | {'статус':<10}"
        print(header)
        print("-" * len(header))
        for i, task in enumerate(tasks, start=1):
            status = "виконано" if task.completed else "активне"
            deadline_str = task.deadline.strftime("%Y-%m-%d")
            print(f"{i:<3} | {task.title:<26} | {task.priority:<6} | {deadline_str:<10} | {status:<10}")

    def show_message(self, message: str):
        print(f"[info] {message}")

    def show_statistics(self, stats: dict):
        print("\n=== статистика ===")
        print(f"  всього: {stats['total']}")
        print(f"  виконано: {stats['completed']}")
        print(f"  активних: {stats['active']}")


# --- controller ---

class TaskController:
    #контролер: зв'язок між model та view і керування стратегією сортування
    def __init__(self, model: TaskModel, view: TaskView):
        self._model = model
        self._view = view
        self._sort_strategy: SortStrategy = SortByPriority()

        # підписка на події моделі (observer)
        self._model.on("task_added", lambda task: self._view.show_message(f"додано завдання: '{task.title}'"))
        self._model.on("task_completed", lambda task: self._view.show_message(f"виконано завдання: '{task.title}'"))
        self._model.on("task_removed", lambda task: self._view.show_message(f"видалено завдання: '{task.title}'"))

    def set_sort_strategy(self, strategy: SortStrategy):
        self._sort_strategy = strategy

    def add_task(self, title: str, priority: int, deadline: datetime):
        self._model.add_task(title, priority, deadline)

    def complete_task(self, index: int):
        self._model.complete_task(index)

    def remove_task(self, index: int):
        self._model.remove_task(index)

    def show_all(self, title: str = "усі завдання"):
        tasks = self._model.get_tasks()
        sorted_tasks = self._sort_strategy.sort(tasks)
        self._view.show_tasks(sorted_tasks, title=title)

    def show_active(self):
        tasks = self._model.get_tasks(include_completed=False)
        sorted_tasks = self._sort_strategy.sort(tasks)
        self._view.show_tasks(sorted_tasks, title="активні завдання")

    def show_stats(self):
        self._view.show_statistics(self._model.get_statistics())


def main():
    model = TaskModel()
    view = TaskView()
    ctrl = TaskController(model, view)

    now = datetime.now()

    #додаємо 5 завдань з різними пріоритетами та дедлайнами
    ctrl.add_task("здати пр3 з python", 1, now + timedelta(days=2))
    ctrl.add_task("купити продукти", 4, now + timedelta(days=1))
    ctrl.add_task("підготуватися до тесту", 2, now + timedelta(days=5))
    ctrl.add_task("оновити репозиторій", 3, now + timedelta(days=3))
    ctrl.add_task("прочитати документацію", 5, now + timedelta(days=7))

    #вивід за пріоритетом (стратегія за замовчуванням)
    ctrl.show_all(title="сортування за пріоритетом")

    # динамічна зміна стратегії на сортування за дедлайном
    ctrl.set_sort_strategy(SortByDeadline())
    ctrl.show_all(title="сортування за дедлайном")

    # позначаємо перше завдання як виконане
    print()
    ctrl.complete_task(0)

    #виводимо лише активні завдання та загальну статистику
    ctrl.show_active()
    ctrl.show_stats()


if __name__ == "__main__":
    main()