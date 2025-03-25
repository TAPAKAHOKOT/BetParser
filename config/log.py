import sys

from loguru import logger

# Пример: выводить логи в консоль
logger.remove()  # Удаляем стандартный обработчик loguru
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>",
    level="DEBUG",
)

# Пример: параллельно логировать в файл с ротацией
logger.add(
    "logs/app.log",
    rotation="10 MB",  # Когда файл достигнет 10 МБ, лог будет архивироваться
    retention="10 days",  # Хранить старые логи 10 дней (по желанию)
    level="INFO",
    encoding="utf-8",
)
