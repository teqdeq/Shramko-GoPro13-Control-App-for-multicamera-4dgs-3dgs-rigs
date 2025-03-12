from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

@dataclass
class FileInfo:
    """Информация о файле"""
    name: str  # Имя файла с префиксом camera_id
    path: str  # Путь к файлу
    size: int  # Размер файла в байтах
    created_at: datetime  # Время создания
    camera_id: str  # ID камеры
    is_sequence: bool = False  # Является ли файл частью последовательности
    group_id: Optional[str] = None  # ID группы файлов
    file_type: str = ""  # Тип файла
    status: str = "pending"  # pending, copying, completed, error
    progress: float = 0.0  # Прогресс копирования (0-100)
    error_message: str = ""  # Сообщение об ошибке
    scene_id: Optional[str] = None  # ID сцены

    @property
    def original_name(self) -> str:
        """Оригинальное имя файла без префикса"""
        if self.name.startswith(f"{self.camera_id}_"):
            return self.name[len(self.camera_id) + 1:]
        return self.name

    @property
    def prefixed_name(self) -> str:
        """Имя файла с префиксом camera_id"""
        if not self.name.startswith(f"{self.camera_id}_"):
            return f"{self.camera_id}_{self.name}"
        return self.name

    @staticmethod
    def split_prefixed_name(name: str) -> Tuple[str, str]:
        """Разделить префиксированное имя на camera_id и оригинальное имя"""
        parts = name.split('_', 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return '', name

@dataclass
class SceneInfo:
    """Информация о сцене (группе файлов)"""
    id: str
    name: str
    created_at: datetime
    files: List[FileInfo]
    total_size: int = 0
    status: str = "pending"  # pending, copying, completed, error
    
    def __post_init__(self):
        self.total_size = sum(f.size for f in self.files)
        
    def get_progress(self) -> float:
        """Получить общий прогресс копирования сцены"""
        if not self.files:
            return 0.0
        return sum(f.progress for f in self.files) / len(self.files)

class FileStatistics:
    """Класс для сбора статистики копирования"""
    def __init__(self):
        self.total_files: int = 0
        self.copied_files: int = 0
        self.failed_files: int = 0
        self.total_size: int = 0
        self.copied_size: int = 0
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
    def start(self):
        """Начало сессии копирования"""
        self.start_time = datetime.now()
        
    def finish(self):
        """Завершение сессии копирования"""
        self.end_time = datetime.now()
        
    def get_duration(self) -> float:
        """Получить длительность копирования в секундах"""
        if not self.start_time:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
        
    def get_speed(self) -> float:
        """Получить среднюю скорость копирования (байт/сек)"""
        duration = self.get_duration()
        if duration == 0:
            return 0.0
        return self.copied_size / duration 