# завдання 2.1. декоратори функцій з параметрами

import functools
import time


def cache(max_size: int = 128):
    #декоратор кешування результатів (спрощений lru-кеш)
    def decorator(func):
        _cache = {}
        _call_order = []
        _stats = {"hits": 0, "misses": 0}

        @functools.wraps(func)
        def wrapper(*args):
            if args in _cache:
                _stats["hits"] += 1
                #оновлюємо позицію в порядку використання
                _call_order.remove(args)
                _call_order.append(args)
                return _cache[args]

            _stats["misses"] += 1
            result = func(*args)

            #якщо кеш заповнений, видаляємо найстаріший запис
            if len(_cache) >= max_size:
                oldest = _call_order.pop(0)
                del _cache[oldest]

            _cache[args] = result
            _call_order.append(args)
            return result

        wrapper.cache_info = lambda: {
            "size": len(_cache),
            "max_size": max_size,
            "hits": _stats["hits"],
            "misses": _stats["misses"],
        }
        wrapper.cache_clear = lambda: (
            _cache.clear(),
            _call_order.clear(),
            _stats.update({"hits": 0, "misses": 0}),
        )
        return wrapper

    return decorator


def rate_limit(max_calls: int, period: float = 60.0):
    #декоратор обмеження частоти викликів функції
    def decorator(func):
        call_times = []

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            #прибираємо виклики, старші за заданий період
            call_times[:] = [t for t in call_times if now - t < period]

            if len(call_times) >= max_calls:
                raise RuntimeError(
                    f"перевищено ліміт викликів {func.__name__}: не більше {max_calls} за {period} с"
                )

            call_times.append(now)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def log(level: str = "INFO"):
    #декоратор логування виклику, часу виконання та помилок
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"[{level.lower()}] виклик {func.__name__}(args={args}, kwargs={kwargs})")
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                print(f"[error] {func.__name__} завершилася з помилкою: {e} (час: {elapsed:.6f} с)")
                raise
            elapsed = time.perf_counter() - start_time
            print(f"[{level.lower()}] {func.__name__} -> {result} (час: {elapsed:.6f} с)")
            return result

        return wrapper

    return decorator


@cache(max_size=64)
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


@rate_limit(max_calls=5, period=10.0)
def send_notification(message: str) -> str:
    return f"надіслано: {message}"


@log(level="DEBUG")
def divide(a: float, b: float) -> float:
    return a / b


def main():
    #1) перевірка декоратора @cache
    print("--- 1. декоратор @cache ---")
    res1 = fibonacci(30)
    print(f"fibonacci(30) = {res1}")
    print(f"статистика після першого виклику: {fibonacci.cache_info()}")

    res2 = fibonacci(30)
    print(f"повторний виклик fibonacci(30) = {res2}")
    print(f"статистика після повторного виклику: {fibonacci.cache_info()}")

    #2) перевірка декоратора @rate_limit
    print("\n--- 2. декоратор @rate_limit ---")
    for i in range(1, 7):
        try:
            status = send_notification(f"повідомлення #{i}")
            print(f"  виклик {i}: {status}")
        except RuntimeError as e:
            print(f"  виклик {i}: перехоплено помилку - {e}")

    # 3) перевірка декоратора @log
    print("\n--- 3. декоратор @log ---")
    divide(10, 3)
    try:
        divide(10, 0)
    except ZeroDivisionError:
        print("помилку ділення на нуль оброблено в main")


if __name__ == "__main__":
    main()