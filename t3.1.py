# завдання 3.1. паттерни Singleton та Factory Method

import json
from abc import ABC, abstractmethod
from datetime import datetime


class SingletonMeta(type):
    #метаклас для реалізації патерну singleton
    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class LogFormatter(ABC):
    @abstractmethod
    def format(self, level: str, message: str, timestamp: datetime) -> str:
        pass


class PlainFormatter(LogFormatter):
    #простий текстовий формат: [рівень] час - повідомлення
    def format(self, level: str, message: str, timestamp: datetime) -> str:
        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return f"[{level}] {time_str} - {message}"


class JSONFormatter(LogFormatter):
    # json-формат
    def format(self, level: str, message: str, timestamp: datetime) -> str:
        payload = {
            "level": level,
            "time": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "message": message,
        }
        return json.dumps(payload, ensure_ascii=False)


class ColorFormatter(LogFormatter):
    # кольоровий формат для терміналу з ansi-кодами
    COLORS = {
        "DEBUG": "\033[90m",
        "INFO": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
    }
    RESET = "\033[0m"

    def format(self, level: str, message: str, timestamp: datetime) -> str:
        color = self.COLORS.get(level, "")
        time_str = timestamp.strftime("%H:%M:%S")
        return f"{color}[{level}] {time_str} - {message}{self.RESET}"


class ShortFormatter(LogFormatter):
    # додатковий форматер для демонстрації реєстрації у фабриці (open/closed)
    def format(self, level: str, message: str, timestamp: datetime) -> str:
        return f"{level[0]}: {message}"


class FormatterFactory:
    _formatters: dict[str, type[LogFormatter]] = {
        "plain": PlainFormatter,
        "json": JSONFormatter,
        "color": ColorFormatter,
    }

    @classmethod
    def register(cls, name: str, formatter_cls: type[LogFormatter]):
        if not issubclass(formatter_cls, LogFormatter):
            raise TypeError("форматер має наслідувати від LogFormatter")
        cls._formatters[name.lower()] = formatter_cls

    @classmethod
    def create(cls, name: str) -> LogFormatter:
        key = name.lower()
        if key not in cls._formatters:
            raise ValueError(f"невідомий форматер: '{name}'")
        return cls._formatters[key]()

    @classmethod
    def available(cls) -> list[str]:
        return list(cls._formatters.keys())


class Logger(metaclass=SingletonMeta):
    LEVELS = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}

    def __init__(self, formatter_name: str = "plain", min_level: str = "DEBUG"):
        self._formatter = FormatterFactory.create(formatter_name)
        self._min_level = min_level.upper()
        self._log_history: list[str] = []

    def set_formatter(self, name: str):
        self._formatter = FormatterFactory.create(name)

    def set_min_level(self, min_level: str):
        level_upper = min_level.upper()
        if level_upper not in self.LEVELS:
            raise ValueError(f"невідомий рівень логування: '{min_level}'")
        self._min_level = level_upper

    def log(self, level: str, message: str):
        level_upper = level.upper()
        if level_upper not in self.LEVELS:
            raise ValueError(f"невідомий рівень логування: '{level}'")
        if self.LEVELS[level_upper] < self.LEVELS[self._min_level]:
            return
        formatted = self._formatter.format(level_upper, message, datetime.now())
        self._log_history.append(formatted)
        print(formatted)

    def debug(self, msg: str):
        self.log("DEBUG", msg)

    def info(self, msg: str):
        self.log("INFO", msg)

    def warning(self, msg: str):
        self.log("WARNING", msg)

    def error(self, msg: str):
        self.log("ERROR", msg)

    def get_history(self) -> list[str]:
        return self._log_history[:]


def main():
    #перевірка singleton
    logger1 = Logger("plain", "DEBUG")
    logger2 = Logger("json", "INFO")
    print(f"singleton (logger1 is logger2): {logger1 is logger2}")

    # вивід у простому форматі
    print("\n--- формат plain ---")
    logger1.info("система запущена")
    logger1.warning("мало пам'яті")
    logger1.error("помилка з'єднання")

    # перемикання на json
    print("\n--- формат json ---")
    logger1.set_formatter("json")
    logger1.debug("діагностика параметрів")
    logger2.info("запис через logger2 у той самий екземпляр")

    #перемикання на кольоровий формат
    print("\n--- формат color ---")
    logger1.set_formatter("color")
    logger1.debug("налагодження")
    logger1.info("успішна операція")
    logger1.warning("попередження")
    logger1.error("критична помилка")

    #реєстрація нового форматера без зміни коду фабрики
    print("\n--- реєстрація нового форматера (short) ---")
    FormatterFactory.register("short", ShortFormatter)
    logger1.set_formatter("short")
    logger1.info("коротке повідомлення")

    #перевірка помилки для невідомого форматера
    try:
        FormatterFactory.create("xml")
    except ValueError as e:
        print(f"очікувана помилка фабрики: {e}")

    print(f"\nдоступні форматери: {FormatterFactory.available()}")
    print(f"записів в історії: {len(logger1.get_history())}")


if __name__ == "__main__":
    main()