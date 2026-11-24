# завдання 2.2. декоратори класів

import functools


def auto_repr(cls):
    #знаходимо оригінальний __init__ (на випадок комбінування з іншими декораторами)
    init_func = cls.__init__
    while hasattr(init_func, "__wrapped__"):
        init_func = init_func.__wrapped__

    #беремо лише імена параметрів конструктора без self
    arg_count = init_func.__code__.co_argcount
    param_names = init_func.__code__.co_varnames[1:arg_count]

    def __repr__(self):
        parts = [f"{name}={getattr(self, name, None)!r}" for name in param_names]
        return f"{cls.__name__}({', '.join(parts)})"

    cls.__repr__ = __repr__
    return cls


def frozen(cls):
    orig_init = cls.__init__

    @functools.wraps(orig_init)
    def new_init(self, *args, **kwargs):
        object.__setattr__(self, "_frozen", False)
        orig_init(self, *args, **kwargs)
        object.__setattr__(self, "_frozen", True)

    def new_setattr(self, name, value):
        if getattr(self, "_frozen", False):
            raise AttributeError(
                f"неможливо змінити атрибут '{name}': об'єкт {cls.__name__} заморожений"
            )
        object.__setattr__(self, name, value)

    cls.__init__ = new_init
    cls.__setattr__ = new_setattr
    return cls


def log_methods(cls):
    for attr_name, attr_value in list(cls.__dict__.items()):
        #обгортаємо лише публічні методи
        if not attr_name.startswith("_") and callable(attr_value):
            def make_wrapper(func):
                @functools.wraps(func)
                def wrapper(self, *args, **kwargs):
                    print(f"[log] {cls.__name__}.{func.__name__}(args={args}, kwargs={kwargs})")
                    try:
                        result = func(self, *args, **kwargs)
                    except Exception as e:
                        print(f"[log] {cls.__name__}.{func.__name__} -> помилка: {e}")
                        raise
                    print(f"[log] {cls.__name__}.{func.__name__} -> {result}")
                    return result

                return wrapper

            setattr(cls, attr_name, make_wrapper(attr_value))
    return cls


@auto_repr
class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance_to(self, other: "Point") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


@frozen
class ImmutableConfig:
    def __init__(self, host: str, port: int, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug


@log_methods
class MathService:
    def add(self, a: float, b: float) -> float:
        return a + b

    def multiply(self, a: float, b: float) -> float:
        return a * b

    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("ділення на нуль")
        return a / b


# демонстрація комбінування всіх трьох декораторів разом
@log_methods
@frozen
@auto_repr
class FrozenVector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def length(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5


def main():
    print("--- 1. декоратор @auto_repr ---")
    p1 = Point(3.0, 4.0)
    p2 = Point(0.0, 0.0)
    print(f"repr(p1): {repr(p1)}")
    print(f"відстань до p2: {p1.distance_to(p2)}")

    print("\n--- 2. декоратор @frozen ---")
    cfg = ImmutableConfig("localhost", 8080, debug=True)
    print(f"config: {cfg.host}:{cfg.port}, debug={cfg.debug}")
    try:
        cfg.host = "remote"
    except AttributeError as e:
        print(f"очікувана помилка: {e}")

    print("\n--- 3. декоратор @log_methods ---")
    svc = MathService()
    svc.add(10, 20)
    svc.multiply(3, 7)
    try:
        svc.divide(10, 0)
    except ValueError:
        print("помилку ValueError перехоплено в main")

    print("\n--- 4. комбінування декораторів ---")
    vec = FrozenVector(3.0, 4.0)
    print(f"repr(vec): {repr(vec)}")
    vec.length()
    try:
        vec.x = 10.0
    except AttributeError as e:
        print(f"очікувана помилка: {e}")


if __name__ == "__main__":
    main()