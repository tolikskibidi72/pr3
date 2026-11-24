# завдання 1.2. типізовані дескриптори та __init_subclass__ для системи конфігурації


class ValidatedField:
    def __init__(self, expected_type: type, min_value=None, max_value=None):
        self.expected_type = expected_type
        self.min_value = min_value
        self.max_value = max_value

    def __set_name__(self, owner, name):
        #зберігаємо публічне та приватне ім'я атрибута
        self.public_name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name, None)

    def __set__(self, obj, value):
        # перевірка типу (враховуємо, що bool у python є підкласом int)
        if not isinstance(value, self.expected_type) or (
            self.expected_type is int and isinstance(value, bool)
        ):
            raise TypeError(
                f"поле '{self.public_name}' очікує тип {self.expected_type.__name__}, "
                f"отримано {type(value).__name__}"
            )

        #перевірка мінімальної межі
        if self.min_value is not None and value < self.min_value:
            raise ValueError(
                f"поле '{self.public_name}' не може бути меншим за {self.min_value} (отримано {value})"
            )

        #перевірка максимальної межі
        if self.max_value is not None and value > self.max_value:
            raise ValueError(
                f"поле '{self.public_name}' не може бути більшим за {self.max_value} (отримано {value})"
            )

        setattr(obj, self.private_name, value)


class ConfigSection:
    _sections: dict[str, type] = {}

    def __init_subclass__(cls, section_name: str = "", **kwargs):
        super().__init_subclass__(**kwargs)
        if section_name:
            cls._sections[section_name] = cls

    @classmethod
    def get_section(cls, name: str):
        if name not in cls._sections:
            raise KeyError(f"секцію '{name}' не знайдено")
        return cls._sections[name]

    @classmethod
    def list_sections(cls) -> list[str]:
        return list(cls._sections.keys())


class DatabaseConfig(ConfigSection, section_name="database"):
    host = ValidatedField(str)
    port = ValidatedField(int, min_value=1, max_value=65535)
    max_connections = ValidatedField(int, min_value=1, max_value=1000)

    def __init__(self, host: str, port: int, max_connections: int):
        self.host = host
        self.port = port
        self.max_connections = max_connections


class LoggingConfig(ConfigSection, section_name="logging"):
    level = ValidatedField(str)
    max_file_size_mb = ValidatedField(int, min_value=1, max_value=1024)

    def __init__(self, level: str, max_file_size_mb: int):
        self.level = level
        self.max_file_size_mb = max_file_size_mb


def main():
    # виводимо список усіх зареєстрованих секцій
    print(f"зареєстровані секції: {ConfigSection.list_sections()}")
    db_cls = ConfigSection.get_section("database")
    print(f"клас для секції 'database': {db_cls.__name__}")

    #створення коректних конфігурацій
    db = DatabaseConfig("localhost", 5432, 100)
    log = LoggingConfig("info", 50)
    print(f"\nналаштування бд: host={db.host}, port={db.port}, max_connections={db.max_connections}")
    print(f"налаштування логів: level={log.level}, max_file_size_mb={log.max_file_size_mb}")

    # перевірка помилки типу (TypeError)
    print("\nспроба встановити невірний тип для port:")
    try:
        db.port = "5432"
    except TypeError as e:
        print(f"  перехоплено помилку: {e}")

    #перевірка виходу за межі діапазону (ValueError)
    print("\nспроба встановити port поза діапазоном:")
    try:
        db.port = 70000
    except ValueError as e:
        print(f"  перехоплено помилку: {e}")

    print("\nспроба встановити некоректний max_file_size_mb:")
    try:
        log.max_file_size_mb = 0
    except ValueError as e:
        print(f"  перехоплено помилку: {e}")


if __name__ == "__main__":
    main()