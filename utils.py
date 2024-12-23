import os
import sys
import logging
from pathlib import Path
from datetime import datetime

def get_app_root() -> Path:
    """Получение корневой директории приложения"""
    if getattr(sys, 'frozen', False):
        # Для скомпилированного приложения
        return Path(sys.executable).parent
    else:
        # Для разработки
        return Path(__file__).parent

def get_data_dir() -> Path:
    """Получение директории для данных"""
    data_dir = get_app_root() / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def get_logs_dir() -> Path:
    """Получение директории для логов"""
    logs_dir = get_app_root() / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

def setup_logging(name: str = None) -> logging.Logger:
    """Настройка логирования
    
    Args:
        name: Имя логгера (опционально)
    
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Создаем директорию для логов
    logs_dir = get_logs_dir()
    
    # Формируем имя файла лога
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"gopro_control_{timestamp}.log"
    
    # Получаем или создаем логгер
    logger = logging.getLogger(name) if name else logging.getLogger()
    
    # Если логгер уже настроен, возвращаем его
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG)
    
    # Форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Хендлер для файла
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Хендлер для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def check_dependencies():
    """Проверка наличия необходимых зависимостей"""
    try:
        import PyQt5
        import requests
        import humanize
        import zeroconf
    except ImportError as e:
        logging.error(f"Missing dependency: {e}")
        raise

def ensure_dir(path: Path):
    """Создание директории если не существует"""
    path.mkdir(parents=True, exist_ok=True)