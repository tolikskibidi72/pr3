# завдання 1.1. система плагінів з автоматичною реєстрацією через метаклас

import hashlib
from abc import abstractmethod


class PluginMeta(type):
    _registry: dict[str, type] = {}
    REQUIRED_ATTRS = ("name", "version")

    def __new__(mcs, cls_name: str, bases: tuple, namespace: dict):
        cls = super().__new__(mcs, cls_name, bases, namespace)

        #перевіряємо лише підкласи, пропускаючи базовий клас
        if bases:
            for attr in mcs.REQUIRED_ATTRS:
                if attr not in namespace:
                    raise TypeError(
                        f"клас {cls_name} повинен визначати обов'язковий атрибут '{attr}'"
                    )
            mcs._registry[cls.name] = cls

        return cls

    @classmethod
    def get_registry(mcs) -> dict[str, type]:
        #повертаємо копію реєстру
        return dict(mcs._registry)

    @classmethod
    def create_plugin(mcs, plugin_name: str):
        #створюємо екземпляр плагіна за його назвою
        if plugin_name not in mcs._registry:
            raise ValueError(f"плагін '{plugin_name}' не знайдено у реєстрі")
        return mcs._registry[plugin_name]()


class BasePlugin(metaclass=PluginMeta):
    @abstractmethod
    def execute(self, data: str) -> str:
        pass


class UpperPlugin(BasePlugin):
    name = "upper"
    version = "1.0"

    def execute(self, data: str) -> str:
        return data.upper()


class ReversePlugin(BasePlugin):
    name = "reverse"
    version = "1.0"

    def execute(self, data: str) -> str:
        return data[::-1]


class CensorPlugin(BasePlugin):
    name = "censor"
    version = "1.1"
    banned_words = ("спам", "реклама")

    def execute(self, data: str) -> str:
        result = data
        for word in self.banned_words:
            result = result.replace(word, "***")
        return result


#динамічне створення класу через type() у тризначній формі
def _hash_execute(self, data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]


HashPlugin = type(
    "HashPlugin",
    (BasePlugin,),
    {
        "name": "hash",
        "version": "2.0",
        "execute": _hash_execute,
    },
)


def main():
    print("зареєстровані плагіни:")
    for name, cls in PluginMeta.get_registry().items():
        print(f"  {name} (v{cls.version}): {cls.__name__}")

    test_data = "привіт світ, це спам"
    print(f"\nвхідні дані: '{test_data}'")
    print("результати виконання плагінів:")
    for name in PluginMeta.get_registry():
        plugin = PluginMeta.create_plugin(name)
        print(f"  {name}: {plugin.execute(test_data)}")

    print("\nперевірка валідації (клас без атрибута version):")
    try:
        class BrokenPlugin(BasePlugin):
            name = "broken"

            def execute(self, data: str) -> str:
                return data
    except TypeError as e:
        print(f"  перехоплено помилку: {e}")


if __name__ == "__main__":
    main()