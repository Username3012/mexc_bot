"""Настройка логирования с выводом в консоль и файл."""

import logging
import sys
import structlog
from datetime import datetime


def configure_logging(level="INFO", json_format=False, log_file=None):
    """Настройка логирования с выводом в консоль."""
    
    # Настройка стандартного logging для консоли
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, level.upper()),
        stream=sys.stdout,
        force=True  # Принудительно перенастраиваем
    )
    
    # Настройка structlog
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Человекочитаемый вывод
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    logger = structlog.get_logger()
    
    # Добавляем запись в файл
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        logging.getLogger().addHandler(file_handler)
    
    # ПРЯМОЙ ВЫВОД В КОНСОЛЬ
    print(f"✅ Логирование настроено (уровень: {level})")
    print(f"   Вывод в консоль: ВКЛЮЧЕН")
    if log_file:
        print(f"   Вывод в файл: {log_file}")
    
    return logger


# Функция для принудительного вывода в консоль
def console_print(message, level="INFO"):
    """Принудительный вывод в консоль."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")
    sys.stdout.flush()  # Принудительный сброс буфера