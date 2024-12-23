from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging
from utils import get_data_dir

@dataclass
class FileInfo:
    name: str
    size: int
    camera_sn: str
    camera_ip: str
    folder: str
    timestamp: datetime
    status: str  # 'pending', 'copying', 'copied', 'failed', 'skipped'
    progress: float = 0.0  # Прогресс копирования в процентах
    error_message: Optional[str] = None

@dataclass
class SceneInfo:
    name: str
    timestamp: datetime
    files: List[FileInfo]
    total_size: int = 0
    
    def calculate_stats(self) -> Dict:
        copied = len([f for f in self.files if f.status == 'copied'])
        failed = len([f for f in self.files if f.status == 'failed'])
        skipped = len([f for f in self.files if f.status == 'skipped'])
        copying = len([f for f in self.files if f.status == 'copying'])
        pending = len([f for f in self.files if f.status == 'pending'])
        
        # Вычисляем общий прогресс сцены
        total_progress = 0
        if self.files:
            total_progress = sum(f.progress for f in self.files) / len(self.files)
        
        return {
            'total': len(self.files),
            'copied': copied,
            'failed': failed,
            'skipped': skipped,
            'copying': copying,
            'pending': pending,
            'progress': total_progress,
            'total_size': self.total_size
        }

class CopyStatistics:
    def __init__(self):
        self.scenes: List[SceneInfo] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.current_scene: Optional[SceneInfo] = None
        self.current_file: Optional[FileInfo] = None
        
    def start_session(self):
        self.start_time = datetime.now()
        
    def end_session(self):
        self.end_time = datetime.now()
        
    def add_scene(self, scene: SceneInfo):
        self.scenes.append(scene)
        
    def update_file_progress(self, file_name: str, progress: float):
        """Обновление прогресса копирования файла"""
        if self.current_scene:
            for file in self.current_scene.files:
                if file.name == file_name:
                    file.progress = progress
                    if progress >= 100:
                        file.status = 'copied'
                    elif progress > 0:
                        file.status = 'copying'
                    break
        
    def get_summary(self) -> Dict:
        total_files = sum(len(scene.files) for scene in self.scenes)
        total_copied = sum(
            len([f for f in scene.files if f.status == 'copied'])
            for scene in self.scenes
        )
        total_failed = sum(
            len([f for f in scene.files if f.status == 'failed'])
            for scene in self.scenes
        )
        total_size = sum(scene.total_size for scene in self.scenes)
        
        # Вычисляем общий прогресс
        total_progress = 0
        if self.scenes:
            scene_progresses = [
                scene.calculate_stats()['progress']
                for scene in self.scenes
            ]
            total_progress = sum(scene_progresses) / len(scene_progresses)
        
        return {
            'total_scenes': len(self.scenes),
            'total_files': total_files,
            'copied_files': total_copied,
            'failed_files': total_failed,
            'total_size': total_size,
            'total_progress': total_progress,
            'duration': (self.end_time - self.start_time).total_seconds() if self.end_time else None,
            'current_scene': self.current_scene.name if self.current_scene else None,
            'current_file': self.current_file.name if self.current_file else None
        }
    
    def save_report(self, destination: Path):
        report_file = destination / f'copy_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"Copy Report - {datetime.now()}\n")
            f.write("=" * 50 + "\n\n")
            
            summary = self.get_summary()
            f.write("Summary:\n")
            f.write(f"Total Scenes: {summary['total_scenes']}\n")
            f.write(f"Total Files: {summary['total_files']}\n")
            f.write(f"Copied Files: {summary['copied_files']}\n")
            f.write(f"Failed Files: {summary['failed_files']}\n")
            f.write(f"Total Size: {summary['total_size'] / (1024*1024):.2f} MB\n")
            if summary['duration']:
                f.write(f"Duration: {summary['duration']:.2f} seconds\n")
            
            f.write("\nDetailed Scene Information:\n")
            for scene in self.scenes:
                f.write(f"\nScene: {scene.name}\n")
                stats = scene.calculate_stats()
                f.write(f"Files: {stats['total']}\n")
                f.write(f"Copied: {stats['copied']}\n")
                f.write(f"Failed: {stats['failed']}\n")
                f.write(f"Skipped: {stats['skipped']}\n")
                f.write(f"In Progress: {stats['copying']}\n")
                f.write(f"Pending: {stats['pending']}\n")
                f.write(f"Progress: {stats['progress']:.1f}%\n")
                f.write(f"Size: {stats['total_size'] / (1024*1024):.2f} MB\n")
                
                if stats['failed'] > 0:
                    f.write("\nFailed Files:\n")
                    for file in scene.files:
                        if file.status == 'failed':
                            f.write(f"- {file.name}: {file.error_message}\n") 