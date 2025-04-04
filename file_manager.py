from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

@dataclass
class FileInfo:
    """Information about a file"""
    name: str  # File name with the camera_id prefix
    path: str  # File path
    size: int  # File size in bytes
    created_at: datetime  # Creation time
    camera_id: str  # Camera ID
    is_sequence: bool = False  # Whether the file is part of a sequence
    group_id: Optional[str] = None  # File group ID
    file_type: str = ""  # File type
    status: str = "pending"  # pending, copying, completed, error
    progress: float = 0.0  # Copy progress (0-100)
    error_message: str = ""  # Error message
    scene_id: Optional[str] = None  # Scene ID

    @property
    def original_name(self) -> str:
        """Original file name without the prefix"""
        if self.name.startswith(f"{self.camera_id}_"):
            return self.name[len(self.camera_id) + 1:]
        return self.name

    @property
    def prefixed_name(self) -> str:
        """File name with the camera_id prefix"""
        if not self.name.startswith(f"{self.camera_id}_"):
            return f"{self.camera_id}_{self.name}"
        return self.name

    @staticmethod
    def split_prefixed_name(name: str) -> Tuple[str, str]:
        """Split the prefixed name into camera_id and the original name"""
        parts = name.split('_', 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return '', name

@dataclass
class SceneInfo:
    """Information about a scene (group of files)"""
    id: str
    name: str
    created_at: datetime
    files: List[FileInfo]
    total_size: int = 0
    status: str = "pending"  # pending, copying, completed, error
    
    def __post_init__(self):
        self.total_size = sum(f.size for f in self.files)
        
    def get_progress(self) -> float:
        """Get the overall copy progress of the scene"""
        if not self.files:
            return 0.0
        return sum(f.progress for f in self.files) / len(self.files)

class FileStatistics:
    """Class for collecting copy statistics"""
    def __init__(self):
        self.total_files: int = 0
        self.copied_files: int = 0
        self.failed_files: int = 0
        self.total_size: int = 0
        self.copied_size: int = 0
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
    def start(self):
        """Start the copy session"""
        self.start_time = datetime.now()
        
    def finish(self):
        """Finish the copy session"""
        self.end_time = datetime.now()
        
    def get_duration(self) -> float:
        """Get the duration of the copy session in seconds"""
        if not self.start_time:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
        
    def get_speed(self) -> float:
        """Get the average copy speed (bytes/second)"""
        duration = self.get_duration()
        if duration == 0:
            return 0.0
        return self.copied_size / duration