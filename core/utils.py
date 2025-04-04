# core/utils.py

import logging
import os
from typing import Optional

def setup_logger(log_file: str = "ilinks.log") -> None:
    """Настраивает логгер для записи в файл и в консоль."""

    # Создаем папку logs, если ее нет
    log_dir: str = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Полный путь к файлу лога
    log_path: str = os.path.join(log_dir, log_file)

    # Настраиваем базовый логгер
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8"  # Явное указание кодировки
    )

    # Создаем обработчик для вывода в консоль
    console_handler: logging.StreamHandler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter: logging.Formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)

    # Добавляем обработчик в логгер
    logging.getLogger('').addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Возвращает логгер с указанным именем."""
    return logging.getLogger(name)


# Пример использования:
if __name__ == '__main__':
    setup_logger()  # Настраиваем логгер
    logger = get_logger(__name__)  # Получаем логгер для текущего модуля

    logger.info("Это информационное сообщение.")
    logger.warning("Это сообщение-предупреждение.")
    logger.error("Это сообщение об ошибке.")