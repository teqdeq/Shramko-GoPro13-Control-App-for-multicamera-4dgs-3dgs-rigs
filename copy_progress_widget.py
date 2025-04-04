from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QProgressBar,
                            QLabel, QScrollArea, QFrame, QGridLayout,
                            QPushButton, QHBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal
import humanize
from datetime import datetime
import logging
from pathlib import Path
from file_manager import FileInfo

logger = logging.getLogger(__name__)

class SceneProgressWidget(QFrame):
    """Widget for displaying progress for a single scene"""
    def __init__(self, scene_id: str, scene_name: str):
        super().__init__()
        self.scene_id = scene_id
        self.scene_name = scene_name
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Scene header
        header_layout = QHBoxLayout()
        self.title_label = QLabel(f"Scene: {self.scene_name}")
        self.title_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.title_label)
        
        # Scene statistics
        self.stats_label = QLabel()
        header_layout.addWidget(self.stats_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Scene progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        # File table
        self.files_layout = QGridLayout()
        self.files_layout.setColumnStretch(0, 2)  # File name
        self.files_layout.setColumnStretch(1, 1)  # Size
        self.files_layout.setColumnStretch(2, 1)  # Progress
        self.files_layout.setColumnStretch(3, 2)  # Status
        
        # Table headers
        self.files_layout.addWidget(QLabel("File"), 0, 0)
        self.files_layout.addWidget(QLabel("Size"), 0, 1)
        self.files_layout.addWidget(QLabel("Progress"), 0, 2)
        self.files_layout.addWidget(QLabel("Status"), 0, 3)
        
        layout.addLayout(self.files_layout)
        
        self.setLayout(layout)
        
        # Dictionary for storing file widgets
        self.file_widgets = {}
        
    def add_file(self, file_name: str, file_size: int, camera_id: str = None):
        """Add a file to the table"""
        row = len(self.file_widgets) + 1
        
        # Always display the name with a prefix
        display_name = f"{camera_id}_{file_name}" if camera_id else file_name
        
        # Create widgets for the file
        name_label = QLabel(display_name)
        size_label = QLabel(humanize.naturalsize(file_size))
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        status_label = QLabel("Waiting...")
        
        # Check if the file exists
        if hasattr(self, 'scene_dir') and self.scene_dir:
            target_path = self.scene_dir / display_name
            if target_path.exists():
                actual_size = target_path.stat().st_size
                if actual_size == file_size:
                    status_label.setText("Completed")
                    progress_bar.setValue(100)
                    logger.info(f"Found existing file: {display_name}")
                else:
                    logger.warning(f"Size mismatch for {display_name}")
        
        # Add widgets to the table
        self.files_layout.addWidget(name_label, row, 0)
        self.files_layout.addWidget(size_label, row, 1)
        self.files_layout.addWidget(progress_bar, row, 2)
        self.files_layout.addWidget(status_label, row, 3)
        
        # Save widgets
        self.file_widgets[file_name] = {
            'name_label': name_label,
            'progress_bar': progress_bar,
            'status_label': status_label,
            'camera_id': camera_id,
            'size': file_size
        }
        
    def update_file_progress(self, file_name: str, progress: float, status: str = None, camera_id: str = None):
        """Update file progress"""
        if file_name in self.file_widgets:
            widgets = self.file_widgets[file_name]
            widgets['progress_bar'].setValue(int(progress))
            
            # Update status, considering skipped files
            if status:
                if status == "Skipped":
                    widgets['status_label'].setText("Completed")
                    widgets['progress_bar'].setValue(100)
                else:
                    widgets['status_label'].setText(status)
                
            # Update camera_id and displayed name if necessary
            if camera_id and camera_id != widgets.get('camera_id'):
                widgets['camera_id'] = camera_id
                widgets['name_label'].setText(f"{camera_id}_{file_name}")
                logger.info(f"Updated camera_id for file {file_name}")
                
    def update_scene_progress(self, total_files: int, copied_files: int, failed_files: int, total_size: int):
        """Update scene statistics"""
        if total_files > 0:
            progress = (copied_files / total_files) * 100
            self.progress_bar.setValue(int(progress))
            
        stats_text = (
            f"Files: {copied_files}/{total_files} "
            f"({failed_files} failed) "
            f"Total size: {humanize.naturalsize(total_size)}"
        )
        self.stats_label.setText(stats_text)


class CopyProgressWidget(QWidget):
    """Widget for displaying overall copy progress"""
    update_signal = pyqtSignal(dict)  # Signal for updates from another thread
    
    # Signals for controlling the copy process
    pause_signal = pyqtSignal()
    resume_signal = pyqtSignal()
    cancel_signal = pyqtSignal()
    retry_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.scenes = {}  # scene_id -> SceneProgressWidget
        self.is_paused = False
        self.setup_ui()
        self.update_signal.connect(self.handle_update)
        
    def setup_ui(self):
        self.layout = QVBoxLayout()
        
        # General information
        info_layout = QHBoxLayout()
        
        # Overall progress
        progress_layout = QVBoxLayout()
        self.total_label = QLabel("Total Progress")
        self.total_label.setStyleSheet("font-weight: bold;")
        progress_layout.addWidget(self.total_label)
        
        self.total_progress = QProgressBar()
        self.total_progress.setRange(0, 100)
        progress_layout.addWidget(self.total_progress)
        
        info_layout.addLayout(progress_layout)
        
        # Statistics
        stats_layout = QVBoxLayout()
        self.stats_label = QLabel()
        stats_layout.addWidget(self.stats_label)
        
        # Current operation
        self.current_op_label = QLabel()
        self.current_op_label.setStyleSheet("color: blue;")
        stats_layout.addWidget(self.current_op_label)
        
        info_layout.addLayout(stats_layout)
        
        # Control buttons
        control_layout = QVBoxLayout()
        
        # Pause/Resume button
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause)
        control_layout.addWidget(self.pause_button)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_signal.emit)
        control_layout.addWidget(self.cancel_button)
        
        info_layout.addLayout(control_layout)
        
        self.layout.addLayout(info_layout)
        
        # Container for scenes
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scenes_layout = QVBoxLayout(self.scroll_widget)
        
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)
        
        # Set size ratios
        self.layout.setStretch(0, 0)  # info_layout - minimal size
        self.layout.setStretch(1, 1)  # scroll_area - stretches
        
        self.setLayout(self.layout)
        
    def toggle_pause(self):
        """Toggle pause"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.setText("Resume")
            self.pause_signal.emit()
        else:
            self.pause_button.setText("Pause")
            self.resume_signal.emit()
            
    def handle_update(self, data: dict):
        """Handle progress update"""
        # Check operation status
        if "status" in data:
            status = data["status"]
            message = data.get("message", "")
            
            if status == "completed":
                self.current_op_label.setText(message)
                self.current_op_label.setStyleSheet("color: green;")
                # Set progress to 100%
                self.total_progress.setValue(100)
                # Disable control buttons
                self.pause_button.setEnabled(False)
                self.cancel_button.setEnabled(False)
                return
                
            elif status == "cancelled":
                self.current_op_label.setText(message)
                self.current_op_label.setStyleSheet("color: red;")
                # Disable control buttons
                self.pause_button.setEnabled(False)
                self.cancel_button.setEnabled(False)
                return
                
            elif status == "paused":
                self.current_op_label.setText(message)
                self.current_op_label.setStyleSheet("color: orange;")
                return
                
            elif status == "resumed":
                self.current_op_label.setText(message)
                self.current_op_label.setStyleSheet("color: blue;")
                return
                
        # Add new scene
        if "add_scene" in data:
            scene_data = data["add_scene"]
            logger.info(f"Adding scene with data: {scene_data}")
            self.add_scene(
                scene_data["id"],
                scene_data["name"],
                scene_data["files"],
                scene_data.get("scene_dir")  # Fixed from dir to scene_dir
            )
            return
            
        # Update scene progress
        if "scene_progress" in data:
            scene_data = data["scene_progress"]
            scene_id = scene_data["id"]
            
            if scene_id in self.scenes:
                scene_widget = self.scenes[scene_id]
                scene_widget.update_scene_progress(
                    scene_data["total_files"],
                    scene_data["copied_files"],
                    scene_data["failed_files"],
                    scene_data["total_size"]
                )
            return
            
        # Update file information
        if "file" in data:
            file_name = data["file"]
            scene_id = data.get("scene_id")
            
            if scene_id in self.scenes:
                scene_widget = self.scenes[scene_id]
                progress = data.get("progress", 0)
                status = data.get("status", "")
                camera_id = data.get("camera_id")
                
                if not camera_id:
                    logger.warning(f"No camera_id in update for file {file_name}")
                    
                # Immediately update file status
                scene_widget.update_file_progress(file_name, progress, status, camera_id)
                
                # If file is skipped or completed, immediately update overall progress
                if status in ["Completed", "Skipped"]:
                    self.total_progress.setValue(int(progress))
                
            if status not in ["Completed", "Skipped"]:
                self.current_op_label.setText(f"Copying {file_name}: {progress:.1f}%")
                
        # Update overall statistics
        if "total_files" in data:
            total = data["total_files"]
            copied = data["copied_files"]
            failed = data["failed_files"]
            duration = data.get("duration", 0)
            speed = data.get("speed", 0)
            
            # Update overall progress
            if total > 0:
                progress = min((copied / total) * 100, 99.9)  # Prevent reaching 100% until fully completed
                self.total_progress.setValue(int(progress))
                
            # Update statistics
            stats_text = (
                f"Files: {copied}/{total} ({failed} failed)\n"
                f"Duration: {humanize.naturaldelta(duration)}\n"
                f"Speed: {humanize.naturalsize(speed)}/s"
            )
            self.stats_label.setText(stats_text)
            
            # Update operation status in case of errors
            if failed > 0:
                self.current_op_label.setText(f"Copy in progress (with {failed} errors)")
                self.current_op_label.setStyleSheet("color: red;")
                
    def add_scene(self, scene_id: str, scene_name: str, files: list, scene_dir: str = None):
        """Add a new scene"""
        if scene_id not in self.scenes:
            scene_widget = SceneProgressWidget(scene_id, scene_name)
            
            # Set scene directory path
            if scene_dir:
                scene_widget.scene_dir = Path(scene_dir)
                logger.info(f"Set scene_dir for scene {scene_id}: {scene_dir}")
            else:
                logger.warning(f"No scene_dir provided for scene {scene_id}")
            
            # Add files to the scene
            for file_info in files:
                if isinstance(file_info, tuple):
                    file, camera_id = file_info
                    if not camera_id:
                        logger.warning(f"No camera_id for file {file.name}")
                    scene_widget.add_file(file.name, file.size, camera_id)
                else:
                    # For backward compatibility
                    camera_id = getattr(file_info, 'camera_id', None)
                    if not camera_id:
                        logger.warning(f"No camera_id for file {file_info.name}")
                    scene_widget.add_file(file_info.name, file_info.size, camera_id)
                
            self.scenes[scene_id] = scene_widget
            self.scenes_layout.addWidget(scene_widget)
            
    def clear(self):
        """Clear all widgets"""
        for scene_widget in self.scenes.values():
            scene_widget.deleteLater()
        self.scenes.clear()
        self.total_progress.setValue(0)
        self.stats_label.clear()
        self.current_op_label.clear()
        self.pause_button.setText("Pause")
        self.pause_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        self.is_paused = False