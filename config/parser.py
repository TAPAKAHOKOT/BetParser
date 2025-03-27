import json
from pathlib import Path


class ParserConfig:
    """
    Синглтон для хранения настроек приложения.
    Загружает данные из JSON-файла при первом создании.
    """

    _instance = None  # Статическое поле для хранения единственного экземпляра

    def __new__(cls, config_name: str = "parser.json"):
        if cls._instance is None:
            # Если экземпляра ещё нет, создаём его и инициализируем
            cls._instance = super().__new__(cls)

            # Загружаем данные
            cls._instance._init_config(config_name)
        return cls._instance

    def _init_config(self, config_path: str):
        # Внутренний метод для чтения JSON и сохранения в self._data
        config_file = Path(__file__).parent / "json" / config_path
        with open(config_file, "r", encoding="utf-8") as f:
            self._data = json.load(f)

        # Вытаскиваем нужные параметры в отдельные атрибуты
        self.url = self._data.get("url", None)
        self.headless = self._data.get("headless", True)

        # SELECTORS
        self.selectors = self._data.get("selectors", {})

    def get(self, key, default=None):
        """
        Универсальный метод для получения произвольных полей из конфигурации.
        Пример: config.get('some_field', default=123)
        """
        return self._data.get(key, default)
