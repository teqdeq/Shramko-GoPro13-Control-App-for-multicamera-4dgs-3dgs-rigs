from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

@dataclass
class FileInfo:
    """Информация о файле с камеры"""
    name: str
    path: Path
    size: int
    created_at: datetime
    camera_id: str
    scene_id: Optional[str] = None
    status: str = "pending"  # pending, copying, completed, error
    progress: float = 0.0
    error_message: Optional[str] = None

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