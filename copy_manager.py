# Copyright (c) 2024 Andrii Shramko
# Contact: zmei116@gmail.com
# LinkedIn: https://www.linkedin.com/in/andrii-shramko/
# Tags: #ShramkoVR #ShramkoCamera #ShramkoSoft
# License: This code is free to use for non-commercial projects.
# For commercial use, please contact Andrii Shramko at the above email or LinkedIn.

import json
import logging
import shutil
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QTimer
from PyQt5.QtWidgets import QApplication
import time
import os
import sys
from dataclasses import dataclass, field

from file_manager import FileInfo, SceneInfo, FileStatistics

logger = logging.getLogger(__name__)

@dataclass
class SceneInfo:
    """Information about the scene (group of files)"""
    id: str
    name: str
    created_at: datetime
    files: List[FileInfo]
    total_size: int = 0
    status: str = "pending"  # pending, copying, completed, error
    has_jpg: bool = False
    has_gpr: bool = False
    file_counts: Dict[str, int] = field(default_factory=lambda: {"MP4": 0, "JPG": 0, "GPR": 0})
    
    def __post_init__(self):
        self.total_size = sum(f.size for f in self.files)
        # Counting the number of files of each type
        for file in self.files:
            file_type = file.name.split('.')[-1].upper()
            if file_type in self.file_counts:
                self.file_counts[file_type] += 1
                if file_type == 'JPG':
                    self.has_jpg = True
                elif file_type == 'GPR':
                    self.has_gpr = True
        
    def get_progress(self) -> float:
        """Get the overall progress of copying the scene"""
        if not self.files:
            return 0.0
        return sum(f.progress for f in self.files) / len(self.files)
        
    def create_folder_structure(self, base_path: Path):
        """Generates directory structure for the scene"""
        scene_path = base_path / self.name
        scene_path.mkdir(parents=True, exist_ok=True)
        
        # Creates a folder structure for the scene
        if self.has_jpg and self.file_counts['JPG'] > 0:
            jpg_path = scene_path / 'JPG'
            jpg_path.mkdir(exist_ok=True)
            
        if self.has_gpr and self.file_counts['GPR'] > 0:
            gpr_path = scene_path / 'GPR'
            gpr_path.mkdir(exist_ok=True)
            
        return scene_path

class CopyThread(QThread):
    """Thread for copying files"""
    
    # Signals for updating the GUI
    progress_signal = pyqtSignal(dict)  # Copying progress
    error_signal = pyqtSignal(str)      # Errors
    status_signal = pyqtSignal(dict)    # Operation status
    finished_signal = pyqtSignal()      # Completion signal
    
    def __init__(self, manager, target_dir):
        super().__init__()
        self.manager = manager
        self.target_dir = target_dir
        self.is_running = False
        
    def run(self):
        """Start copying in a separate thread"""
        try:
            self.is_running = True
            if self.manager.is_cancelled:
                logger.info("Copy session cancelled before start")
                return
                
            self._copy_files(self.target_dir)
            
        except Exception as e:
            logger.error(f"Error in copy thread: {e}", exc_info=True)
            self.error_signal.emit(f"Copy thread failed: {str(e)}")
        finally:
            self.is_running = False
            if self.manager.is_cancelled:
                self.status_signal.emit({
                    "status": "cancelled",
                    "message": "Copy session cancelled"
                })
            self.finished_signal.emit()
            
    def _copy_files(self, target_dir: Path):
        """Internal method for copying files"""
        try:
            self.manager.statistics.start()
            
            # Checking for pause before starting copying
            while self.manager.is_paused and not self.manager.is_cancelled:
                time.sleep(0.1)  # Reduce the interval for faster response
                
            if self.manager.is_cancelled:
                logger.info("Copy session cancelled during initial pause")
                return
                    
            # Creating scenes in the GUI and checking existing files
            for scene in self.manager.scenes:
                # Checking for operation cancellation
                if self.manager.is_cancelled:
                    logger.info("Copy session cancelled during scene preparation")
                    return
                    
                # Checking for pause
                while self.manager.is_paused and not self.manager.is_cancelled:
                    time.sleep(0.1)
                    
                if self.manager.is_cancelled:
                    return
                    
                scene_files = []
                scene_dir = target_dir / scene.name
                scene_dir.mkdir(parents=True, exist_ok=True)
                
                # First, check all files
                for file in scene.files:
                    # Determining the subfolder depending on the file type
                    file_type = file.name.split('.')[-1].upper()
                    file_name_with_sn = f"{file.camera_id}_{file.name}"
                    
                    if file_type == 'JPG':
                        target_path = scene_dir / 'JPG' / file_name_with_sn
                    elif file_type == 'GPR':
                        target_path = scene_dir / 'GPR' / file_name_with_sn
                    else:
                        target_path = scene_dir / file_name_with_sn
                        
                    # Creating the directory if it does not exist
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if target_path.exists():
                        actual_size = target_path.stat().st_size
                        camera_ip = self.manager.get_camera_ip(file.camera_id)
                        if camera_ip:
                            real_size = self.get_file_size_from_camera(camera_ip, file)
                            if real_size > 0 and actual_size == real_size and target_path.name.startswith(f"{file.camera_id}_"):
                                file.status = "completed"
                                file.progress = 100
                                logger.info(f"File already exists with correct size and camera ID: {file_name_with_sn}")
                    
                    scene_files.append((file, file.camera_id))
                
                # Now sending scene information to the GUI with current statuses
                self.progress_signal.emit({
                    "add_scene": {
                        "id": scene.id,
                        "name": scene.name,
                        "files": scene_files,
                        "scene_dir": str(scene_dir)
                    }
                })
                
                # Checking for pause after adding the scene
                while self.manager.is_paused and not self.manager.is_cancelled:
                    time.sleep(0.1)
                
                # And immediately send statuses for completed files
                for file in scene.files:
                    if file.status == "completed":
                        self.progress_signal.emit({
                            "file": file.name,
                            "progress": 100,
                            "scene_id": scene.id,
                            "status": "Completed",
                            "camera_id": file.camera_id
                        })
            
            # Creating a list of files for copying
            all_files = []
            for scene in self.manager.scenes:
                scene_dir = target_dir / scene.name
                for file in scene.files:
                    if file.status != "completed":  # Skipping already completed files
                        file.scene_id = scene.id
                        all_files.append((file, scene_dir, scene))

            total_files = len(all_files)
            completed = 0
            failed = 0

            # Separating files into videos and photos.
            video_files = [(f, d, s) for f, d, s in all_files if f.name.endswith('.MP4')]
            photo_files = [(f, d, s) for f, d, s in all_files if f.name.endswith('.JPG')]

            # Separating files into videos and photos
            if photo_files:
                with ThreadPoolExecutor(max_workers=min(10, len(photo_files))) as executor:
                    futures = []
                    for file, scene_dir, scene in photo_files:
                        if self.manager.is_cancelled:
                            break
                        future = executor.submit(self.copy_file, file, scene_dir, scene)
                        futures.append(future)
                    
                    # Waiting for all operations to complete
                    for future in futures:
                        try:
                            success = future.result()
                            if success:
                                completed += 1
                                self.manager.statistics.copied_files += 1
                            else:
                                failed += 1
                                self.manager.statistics.failed_files += 1
                            
                            # Updating overall progress
                            self.status_signal.emit({
                                "total_files": total_files,
                                "copied_files": completed,
                                "failed_files": failed,
                                "duration": self.manager.statistics.get_duration(),
                                "speed": self.manager.statistics.get_speed()
                            })
                            
                        except Exception as e:
                            logger.error(f"Error in photo copy thread: {e}")
            
            # Then copy videos (sequentially)
            for file, scene_dir, scene in video_files:
                if self.manager.is_cancelled:
                    break
                try:
                    success = self.copy_file(file, scene_dir, scene)
                    if success:
                        completed += 1
                        self.manager.statistics.copied_files += 1
                    else:
                        failed += 1
                        self.manager.statistics.failed_files += 1
                    
                    # Updating overall progress
                    self.status_signal.emit({
                        "total_files": total_files,
                        "copied_files": completed,
                        "failed_files": failed,
                        "duration": self.manager.statistics.get_duration(),
                        "speed": self.manager.statistics.get_speed()
                    })
                    
                except Exception as e:
                    logger.error(f"Error copying video file: {e}")
                    failed += 1
                    self.manager.statistics.failed_files += 1

            self.manager.statistics.finish()
            
            # Sending the final status
            if self.manager.is_cancelled:
                self.status_signal.emit({
                    "status": "cancelled",
                    "message": "Copy session cancelled",
                    "total_files": total_files,
                    "copied_files": completed,
                    "failed_files": failed,
                    "duration": self.manager.statistics.get_duration(),
                    "speed": self.manager.statistics.get_speed()
                })
            else:
                self.status_signal.emit({
                    "status": "completed",
                    "message": "Copy session completed",
                    "total_files": total_files,
                    "copied_files": completed,
                    "failed_files": failed,
                    "duration": self.manager.statistics.get_duration(),
                    "speed": self.manager.statistics.get_speed()
                })
            
            # After the main copy loop, add:
            if hasattr(self, 'retry_manager') and self.retry_manager.failed_files:
                logger.info(f"Retrying failed files: {len(self.retry_manager.failed_files)}")
                for file_id, data in list(self.retry_manager.failed_files.items()):
                    if self.manager.is_cancelled:
                        break
                    if data['attempts'] < self.retry_manager.max_retries:
                        # Finding the corresponding file and scene
                        for scene in self.manager.scenes:
                            for file in scene.files:
                                if f"{file.camera_id}_{file.name}" == file_id:
                                    self.copy_file(file, target_dir, scene)
                                    break
            
        except Exception as e:
            logger.error(f"Error in copy session: {e}", exc_info=True)
            self.error_signal.emit(f"Copy session failed: {str(e)}")
            self.status_signal.emit({
                "status": "error",
                "message": f"Copy session failed: {str(e)}"
            })

    def get_file_size_from_camera(self, camera_ip: str, file_info: FileInfo) -> int:
        """Obtain the file size from the camera."""
        # For the request to the camera, we use the original path, as the camera does not know about prefixes
        camera_path = file_info.path.split('DCIM/')[1]  # Path relative to DCIM for the request to the camera
        url = f"http://{camera_ip}:8080/videos/DCIM/{camera_path}"
        try:
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                return int(response.headers.get('Content-Length', 0))
            else:
                logging.error(f"Failed to get file size for {file_info.prefixed_name} from camera {camera_ip}: {response.status_code}")
                return 0
        except Exception as e:
            logging.error(f"Error getting file size for {file_info.prefixed_name} from camera {camera_ip}: {e}")
            return 0

    def check_file_exists(self, file: FileInfo, target_dir: Path) -> bool:
        """Checking file existence"""
        file_path = target_dir / file.prefixed_name
        if file_path.exists():
            # Checking camera_id in the file name
            file_camera_id = file_path.name.split('_')[0]
            if file_camera_id != file.camera_id:
                logger.warning(f"Camera ID mismatch for {file.prefixed_name}: expected {file.camera_id}, got {file_camera_id}")
                try:
                    file_path.unlink()
                    logger.info(f"Removed file with incorrect camera ID: {file.prefixed_name}")
                except Exception as e:
                    logger.error(f"Failed to remove file {file.prefixed_name}: {e}")
                return False
            
            # Checking file size
            actual_size = file_path.stat().st_size
            if actual_size != file.size:
                logger.warning(f"Size mismatch for {file.prefixed_name}: expected {file.size}, got {actual_size}")
                try:
                    file_path.unlink()
                    logger.info(f"Removed file with incorrect size: {file.prefixed_name}")
                except Exception as e:
                    logger.error(f"Failed to remove file {file.prefixed_name}: {e}")
                return False

            # Getting the camera's IP address
            camera_ip = self.manager.get_camera_ip(file.camera_id)
            if not camera_ip:
                logger.warning(f"Could not get camera IP for {file.camera_id}")
                return False

            # Checking the file hash
            camera_hash = self.get_file_hash_from_camera(camera_ip, file)
            local_hash = self.get_local_file_hash(file_path)
            
            if camera_hash and local_hash and camera_hash == local_hash:
                logger.info(f"File already exists with correct hash: {file.prefixed_name}")
                return True
            else:
                logger.warning(f"Hash mismatch for {file.prefixed_name}")
                try:
                    file_path.unlink()
                    logger.info(f"Removed file with incorrect hash: {file.prefixed_name}")
                except Exception as e:
                    logger.error(f"Failed to remove file {file.prefixed_name}: {e}")
                return False
        return False

    def copy_file(self, file: FileInfo, target_dir: Path, scene: SceneInfo) -> bool:
        """Copying a single file with progress tracking"""
        if not hasattr(self, 'retry_manager'):
            self.retry_manager = RetryManager()

        temp_path = None
        camera_ip = self.manager.get_camera_ip(file.camera_id)
        
        # Checking the possibility of a retry
        file_id = f"{file.camera_id}_{file.name}"
        if file_id in self.retry_manager.failed_files:
            if self.retry_manager.failed_files[file_id]['attempts'] >= self.retry_manager.max_retries:
                logger.warning(f"Max retries exceeded for {file.prefixed_name}")
                return False
            # Waiting for the required time before the next retry
            time_since_last = time.time() - self.retry_manager.failed_files[file_id]['last_try']
            required_delay = self.retry_manager.retry_delay * (2 ** (self.retry_manager.failed_files[file_id]['attempts'] - 1))
            if time_since_last < required_delay:
                time.sleep(required_delay - time_since_last)

        try:
            if self.manager.is_cancelled:
                logger.info(f"Copy of {file.prefixed_name} cancelled before start")
                return False
            
            while self.manager.is_paused:
                time.sleep(0.5)
                if self.manager.is_cancelled:
                    return False

            if not camera_ip:
                raise Exception(f"Camera IP not found for {file.camera_id}")
            
            camera_path = file.path.split('DCIM/')[1]
            file_url = f"http://{camera_ip}:8080/videos/DCIM/{camera_path}"
            if not file_url:
                raise Exception(f"File URL is empty for {file.prefixed_name}")
            
            file_type = file.original_name.split('.')[-1].upper()
            if file_type in ['JPG', 'GPR']:
                target_path = target_dir / file_type / file.prefixed_name
            else:
                target_path = target_dir / file.prefixed_name
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Checking the existing file by size and hash
            if target_path.exists():
                actual_size = target_path.stat().st_size
                real_size = self.get_file_size_from_camera(camera_ip, file)
                if real_size > 0 and actual_size == real_size:
                    logger.info(f"File already exists with correct size: {file.prefixed_name}")
                    file.status = "completed"
                    file.progress = 100
                    self.progress_signal.emit({
                        "file": file.prefixed_name,
                        "progress": 100,
                        "scene_id": scene.id,
                        "status": "Completed",
                        "camera_id": file.camera_id
                    })
                    return True
                else:
                    target_path.unlink()

            # Copying the file
            temp_path = target_path.with_suffix('.tmp')
            timeout = 30 if file.original_name.endswith('.MP4') else 10
            
            total_size = self.get_file_size_from_camera(camera_ip, file)
            if total_size <= 0:
                total_size = file.size
            
            response = requests.get(file_url, stream=True, timeout=timeout)
            response.raise_for_status()
            
            downloaded_size = 0
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress = int((downloaded_size / total_size) * 100)
                        file.progress = progress
                        
                        if progress % 5 < 1:
                            self.progress_signal.emit({
                                "file": file.prefixed_name,
                                "progress": progress,
                                "scene_id": scene.id,
                                "status": "Copying...",
                                "camera_id": file.camera_id,
                                "retry_count": self.retry_manager.failed_files.get(file_id, {}).get('attempts', 0)
                            })
                        
            # Checking the file size and moving the file"
            actual_size = temp_path.stat().st_size
            if actual_size != total_size:
                raise Exception(f"Size mismatch after copy: expected {total_size}, got {actual_size}")
            
            temp_path.rename(target_path)
            file.status = "completed"
            file.progress = 100
            
            # Successful copy - removing from failed_files
            if file_id in self.retry_manager.failed_files:
                del self.retry_manager.failed_files[file_id]
            
            logger.info(f"Successfully copied {file.prefixed_name}")
            return True

        except Exception as e:
            logger.error(f"Error copying {file.prefixed_name}: {e}")
            # Registering a failed attempt
            if file_id not in self.retry_manager.failed_files:
                self.retry_manager.failed_files[file_id] = {'attempts': 0, 'last_try': 0}
            self.retry_manager.failed_files[file_id]['attempts'] += 1
            self.retry_manager.failed_files[file_id]['last_try'] = time.time()
            
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass
            return False

    def _copy_file(self, source: Path, target: Path, file_info):
        """Copying a single file with progress tracking"""
        try:
            if self.manager.is_cancelled:
                logger.info(f"Copy of {source.name} cancelled before start")
                return False
                
            # Checking for pause before starting file copy
            while self.manager.is_paused and not self.manager.is_cancelled:
                time.sleep(0.1)
                
            if self.manager.is_cancelled:
                logger.info(f"Copy of {source.name} cancelled during pause")
                return False
                
            # Creating parent directories
            target.parent.mkdir(parents=True, exist_ok=True)
            
            # Opening files for copying
            with open(source, 'rb') as src, open(target, 'wb') as dst:
                # Copying data in chunks with progress tracking
                copied = 0
                file_size = source.stat().st_size
                
                while copied < file_size:
                    # Checking for cancellation
                    if self.manager.is_cancelled:
                        logger.info(f"Copy of {source.name} cancelled during copy")
                        return False
                        
                    # Checking for pause
                    while self.manager.is_paused and not self.manager.is_cancelled:
                        time.sleep(0.1)
                        
                    if self.manager.is_cancelled:
                        logger.info(f"Copy of {source.name} cancelled during pause")
                        return False
                        
                    # Copying a block of data
                    chunk = src.read(8192)
                    if not chunk:
                        break
                        
                    dst.write(chunk)
                    copied += len(chunk)
                    
                    # Updating progress
                    progress = int((copied / file_size) * 100)
                    file_info.progress = progress
                    
                    # Sending an update to the GUI
                    self.progress_signal.emit({
                        "update_file": {
                            "scene_id": file_info.scene_id,
                            "name": file_info.name,
                            "progress": progress
                        }
                    })
                    
            return True
            
        except Exception as e:
            logger.error(f"Error copying {source.name}: {e}")
            return False

class CopyManager(QObject):
    """File copy manager for cameras"""
    
    # Signals for updating the GUI
    progress_signal = pyqtSignal(dict)  # Copying progress
    error_signal = pyqtSignal(str)      # Errors
    status_signal = pyqtSignal(dict)    # Operation status
    
    def __init__(self, max_workers: int = 4):
        super().__init__()
        self.config = self.load_config()
        self.max_workers = self.config.get("copy_settings", {}).get("max_workers", max_workers)
        self.statistics = FileStatistics()
        self.scenes: List[SceneInfo] = []
        self.current_session: Optional[Path] = None
        self.is_paused = False
        self.is_cancelled = False
        self.failed_files = []  # List of failed copies for retry attempts
        self.temp_files = []    # List of temporary files for cleanup
        self.progress_file = Path("copy_progress.json")
        self.camera_ips = {}    # Dictionary for storing camera IP addresses
        
        # Initialization of the thread and timer
        self.copy_thread = None
        
    def load_config(self) -> dict:
        """Loading configuration"""
        try:
            config_path = Path("config.json")
            if config_path.exists():
                with open(config_path, "r") as f:
                    return json.load(f)
            else:
                # Default values
                default_config = {
                    "scene_settings": {
                        "max_interval_seconds": 300
                    },
                    "copy_settings": {
                        "max_workers": 4,
                        "retry_count": 3,
                        "retry_delay": 5
                    },
                    "last_target_dir": str(Path.home() / "Downloads")  # Default path
                }
                # Saving the default configuration
                with open(config_path, "w") as f:
                    json.dump(default_config, f, indent=4)
                return default_config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
        
    def save_target_dir(self, target_dir: Path):
        """Saving the last selected directory"""
        try:
            config_path = Path("config.json")
            config = self.config
            config["last_target_dir"] = str(target_dir)
            
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)
            logger.info(f"Saved last target directory: {target_dir}")
            
        except Exception as e:
            logger.error(f"Error saving target directory: {e}")

    def start_copy_session(self, target_dir: Path):
        """Starting the copy process"""
        try:
            # Saving the selected directory
            self.save_target_dir(target_dir)
            
            # Resetting state flags
            self.is_paused = False
            self.is_cancelled = False
            self.failed_files.clear()
            self.temp_files.clear()
            
            if not self.prepare_copy_session(target_dir):
                return
                
            # Creating and starting the copy thread
            self.copy_thread = CopyThread(self, target_dir)
            
            # Connecting signals
            self.copy_thread.progress_signal.connect(self.progress_signal)
            self.copy_thread.error_signal.connect(self.error_signal)
            self.copy_thread.status_signal.connect(self.status_signal)
            self.copy_thread.finished_signal.connect(self._on_copy_finished)
            
            # Starting the copy process
            self.copy_thread.start()
            
        except Exception as e:
            logger.error(f"Error starting copy: {e}", exc_info=True)
            self.error_signal.emit(f"Failed to start copy: {str(e)}")
            self.status_signal.emit({
                "status": "error",
                "message": f"Failed to start copy: {str(e)}"
            })
            
    def pause(self):
        """Pausing copying"""
        if not self.is_paused:
            self.is_paused = True
            logger.info("Copy session paused")
            self.status_signal.emit({
                "status": "paused",
                "message": "Copy session paused"
            })
        
    def resume(self):
        """Resuming copying"""
        if self.is_paused:
            self.is_paused = False
            logger.info("Copy session resumed")
            self.status_signal.emit({
                "status": "resumed",
                "message": "Copy session resumed"
            })
        
    def cancel(self):
        """Canceling copying"""
        if not self.is_cancelled:
            self.is_cancelled = True
            logger.info("Copy session cancelled")
            self.status_signal.emit({
                "status": "cancelled",
                "message": "Copy session cancelled"
            })
            
            # If the copy thread exists, wait for it to finish
            if self.copy_thread and self.copy_thread.isRunning():
                self.copy_thread.wait()
        
    def _on_copy_finished(self):
        """Copy completion handler"""
        self.copy_thread = None
        logger.info("Copy session finished")
        
    def __del__(self):
        """Destructor for cleaning up temporary files"""
        self.cleanup_temp_files() 
        
    def get_camera_media_list(self, camera_ip: str) -> List[Dict]:
        """Getting the list of media files from the camera via API"""
        try:
            logger.info(f"Getting media list from camera {camera_ip}")
            url = f"http://{camera_ip}:8080/gopro/media/list"
            
            logger.debug(f"Sending request to {url}")
            response = requests.get(url, timeout=5)
            logger.debug(f"Response status code: {response.status_code}")
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Response data: {data}")
            media_list = []
            
            # Processing the response structure from the camera
            for media in data.get('media', []):
                directory = media.get('d', '')  # Folder with files
                files = media.get('fs', [])     # List of files in the folder
                logger.debug(f"Processing directory: {directory}, files count: {len(files)}")
                
                for file in files:
                    file['d'] = directory  # Adding directory information to each file
                    media_list.append(file)
            
            logger.info(f"Found {len(media_list)} media files on camera {camera_ip}")
            logger.debug(f"Media list: {media_list}")
            
            return media_list
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get media list from camera {camera_ip}: {e}")
            return []
            
    def load_camera_cache(self) -> List[Dict]:
        """Loading camera cache and retrieving the list of files"""
        try:
            cache_path = Path("camera_cache.json")
            logger.debug(f"Looking for camera cache at: {cache_path.absolute()}")
            
            if not cache_path.exists():
                logger.error(f"Camera cache file not found at: {cache_path.absolute()}")
                return []
                
            with open(cache_path, "r") as f:
                cameras = json.load(f)
                logger.debug(f"Loaded camera cache: {cameras}")
                
                if not isinstance(cameras, list):
                    logger.error(f"Invalid camera cache format. Expected list, got {type(cameras)}")
                    raise ValueError("Camera cache must be a list")
                    
                if not cameras:
                    logger.warning("Camera cache is empty")
                    return []
                    
                # Getting the list of files for each camera
                cameras_with_media = []
                for camera in cameras:
                    camera_ip = camera.get('ip')
                    if not camera_ip:
                        logger.warning(f"No IP address for camera: {camera}")
                        continue
                        
                    media_list = self.get_camera_media_list(camera_ip)
                    if media_list:
                        camera['media'] = media_list
                        cameras_with_media.append(camera)
                    
                return cameras_with_media
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse camera cache: {e}")
        except Exception as e:
            logger.error(f"Error loading camera cache: {e}", exc_info=True)
        return []
            
    def group_files_into_scenes(self, files: List[FileInfo], scene_interval: int = 5) -> List[SceneInfo]:
        """Grouping files into scenes"""
        if not files:
            return []
        
        # First, group files by group_id
        files_by_group = {}
        for file in files:
            if file.group_id:
                if file.group_id not in files_by_group:
                    files_by_group[file.group_id] = []
                files_by_group[file.group_id].append(file)
        
        # Sorting files by creation time, but keeping groups together
        sorted_files = []
        ungrouped_files = [f for f in files if not f.group_id]
        
        # Sorting ungrouped files
        sorted_ungrouped = sorted(ungrouped_files, key=lambda x: (x.created_at, x.camera_id))
        
        # Sorting groups by the time of the first file in the group
        sorted_groups = sorted(
            files_by_group.items(),
            key=lambda x: min(f.created_at for f in x[1])
        )
        
        # Combining files while keeping groups together
        current_ungrouped_idx = 0
        current_group_idx = 0
        
        while current_ungrouped_idx < len(sorted_ungrouped) and current_group_idx < len(sorted_groups):
            ungrouped_time = sorted_ungrouped[current_ungrouped_idx].created_at
            group_time = min(f.created_at for f in sorted_groups[current_group_idx][1])
            
            if ungrouped_time < group_time:
                sorted_files.append(sorted_ungrouped[current_ungrouped_idx])
                current_ungrouped_idx += 1
            else:
                sorted_files.extend(sorted(sorted_groups[current_group_idx][1], key=lambda x: (x.created_at, x.camera_id)))
                current_group_idx += 1
        
        # Adding the remaining files
        while current_ungrouped_idx < len(sorted_ungrouped):
            sorted_files.append(sorted_ungrouped[current_ungrouped_idx])
            current_ungrouped_idx += 1
            
        while current_group_idx < len(sorted_groups):
            sorted_files.extend(sorted(sorted_groups[current_group_idx][1], key=lambda x: (x.created_at, x.camera_id)))
            current_group_idx += 1
        
        scenes = []
        current_scene_files = []
        current_group_id = None
        
        for file in sorted_files:
            # If this is the first file
            if not current_scene_files:
                current_scene_files = [file]
                current_group_id = file.group_id
                continue
            
            # If the file belongs to the same group as the previous files
            if file.group_id and file.group_id == current_group_id:
                current_scene_files.append(file)
                continue
            
            # Checking the time difference with the previous file
            prev_file = current_scene_files[-1]
            time_diff = (file.created_at - prev_file.created_at).total_seconds()
            
            # Create a new scene if:
            # 1. The time difference is greater than the interval AND the files are not from the same group
            # 2. OR the previous group has ended and a new one begins
            if (time_diff > scene_interval and not (file.group_id and file.group_id == current_group_id)) or \
               (current_group_id and file.group_id != current_group_id):
                # Creating a new scene from the accumulated files
                scene_id = f"scene_{len(scenes) + 1}"
                scene_name = f"scene{len(scenes) + 1:02d}_{current_scene_files[0].created_at.strftime('%Y_%m_%d_%H_%M_%S')}"
                
                scene = SceneInfo(
                    id=scene_id,
                    name=scene_name,
                    created_at=current_scene_files[0].created_at,
                    files=current_scene_files
                )
                scenes.append(scene)
                
                # Starting a new scene with the current file
                current_scene_files = [file]
                current_group_id = file.group_id
            else:
                # Adding the file to the current scene
                current_scene_files.append(file)
                if file.group_id:
                    current_group_id = file.group_id
        
        # Adding the last scene
        if current_scene_files:
            scene_id = f"scene_{len(scenes) + 1}"
            scene_name = f"scene{len(scenes) + 1:02d}_{current_scene_files[0].created_at.strftime('%Y_%m_%d_%H_%M_%S')}"
            
            scene = SceneInfo(
                id=scene_id,
                name=scene_name,
                created_at=current_scene_files[0].created_at,
                files=current_scene_files
            )
            scenes.append(scene)
        
        # Logging information about scenes
        logger.info(f"Grouped {len(files)} files into {len(scenes)} scenes")
        for scene in scenes:
            logger.info(f"Scene {scene.name}:")
            logger.info(f"  Total files: {len(scene.files)}")
            logger.info(f"  Time range: {scene.files[0].created_at} - {scene.files[-1].created_at}")
            logger.info(f"  Groups in scene: {set(f.group_id for f in scene.files if f.group_id)}")
            
            # Counting files by type
            file_types = {}
            for file in scene.files:
                file_type = file.name.split('.')[-1].upper()
                if file_type not in file_types:
                    file_types[file_type] = 0
                file_types[file_type] += 1
            
            # Logging the number of files of each type
            for file_type, count in file_types.items():
                logger.info(f"  {file_type} files: {count}")
            
            # Additional logging of intervals between files
            for i in range(1, len(scene.files)):
                time_diff = (scene.files[i].created_at - scene.files[i-1].created_at).total_seconds()
                logger.info(f"  Time diff between files {scene.files[i-1].name} and {scene.files[i].name}: {time_diff}s")
                if scene.files[i].group_id:
                    logger.info(f"    Group ID: {scene.files[i].group_id}")
        
        return scenes
        
    def prepare_copy_session(self, target_dir: Path) -> bool:
        """Preparing the copy session"""
        try:
            logger.info(f"Preparing copy session to: {target_dir}")
            
            # Creating the directory if it does not exist
            target_dir.mkdir(parents=True, exist_ok=True)
            self.current_session = target_dir
            
            # Loading information about cameras
            cameras = self.load_camera_cache()
            if not cameras:
                logger.error("No cameras found in cache")
                self.error_signal.emit("No cameras found in cache")
                return False
            
            logger.info(f"Found {len(cameras)} cameras in cache")
            
            # Collecting information about files
            files = []
            file_names = {}  # Dict[str, List[FileInfo]]
            
            for camera in cameras:
                camera_id = camera.get('name', '')
                camera_ip = camera.get('ip', '')
                # Saving the camera's IP address
                self.camera_ips[camera_id] = camera_ip
                
                try:
                    # Using the correct endpoint to get the list of files
                    media_url = f"http://{camera_ip}:8080/gopro/media/list"
                    response = requests.get(media_url, timeout=10)
                    response.raise_for_status()
                    
                    media_list = response.json().get('media', [])
                    
                    # Processing each directory
                    for directory in media_list:
                        # Checking for operation cancellation
                        if self.is_cancelled:
                            logger.info("Copy session cancelled during file list preparation")
                            return False
                            
                        dir_name = directory.get('d', '')
                        
                        # Processing each file in the directory
                        for file in directory.get('fs', []):
                            file_name = file.get('n', '').upper()
                            created_time = datetime.fromtimestamp(int(file.get('cre', 0)))
                            size = int(file.get('s', 0))
                            group_id = file.get('g')
                            file_type = file.get('t', '')
                            
                            # Checking if the file is part of a sequence
                            if 'b' in file and 'l' in file:  # If there is a start and end of the sequence
                                start_num = int(file['b'])
                                end_num = int(file['l'])
                                missing_numbers = file.get('m', [])
                                
                                # Getting the letter code of the group from the file name
                                group_letters = file_name[2:4] if not file_name.startswith('GX') else None
                                
                                # Generating all files in the sequence
                                for i in range(start_num, end_num + 1):
                                    if i not in missing_numbers:
                                        if group_letters:
                                            original_name = f"GP{group_letters}{i:04d}.JPG"
                                        else:
                                            original_name = f"GX{i:06d}.MP4"
                                            
                                        # Creating a file name with the camera_id prefix
                                        prefixed_name = f"{camera_id}_{original_name}"
                                        file_url = f"http://{camera_ip}:8080/videos/DCIM/{dir_name}/{original_name}"
                                        
                                        logger.info(f"Adding sequence file: {prefixed_name}")
                                        
                                        file_info = FileInfo(
                                            name=prefixed_name,
                                            path=file_url,
                                            size=size,
                                            created_at=created_time,
                                            camera_id=camera_id,
                                            is_sequence=True,
                                            group_id=group_id,
                                            file_type='JPG' if group_letters else 'MP4'
                                        )
                                        files.append(file_info)
                            else:
                                # Processing regular files (leaving as is)
                                file_info = FileInfo(
                                    name=f"{camera_id}_{file_name}",  # Prefixed name
                                    path=f"http://{camera_ip}:8080/videos/DCIM/{dir_name}/{file_name}",
                                    size=size,
                                    created_at=created_time,
                                    camera_id=camera_id,
                                    is_sequence=False,
                                    group_id=group_id,
                                    file_type=file_type
                                )
                                files.append(file_info)
                            
                            # Checking for duplicates
                            if file_name not in file_names:
                                file_names[file_name] = []
                            file_names[file_name].append(file_info)
                
                except Exception as e:
                    logger.error(f"Error getting files from camera {camera_id}: {e}")
                    self.error_signal.emit(f"Error getting files from camera {camera_id}: {e}")
                    continue
                
            # Checking for duplicates
            for original_name, file_list in file_names.items():
                if len(file_list) > 1:
                    camera_ids = [f.camera_id for f in file_list]
                    logger.warning(f"File {original_name} exists in cameras: {', '.join(camera_ids)}")
                
            # Grouping files into scenes
            scenes = self.group_files_into_scenes(files)
            if not scenes:
                logger.error("No scenes found")
                self.error_signal.emit("No scenes found")
                return False
            
            logger.info(f"Grouped {len(files)} files into {len(scenes)} scenes")
            
            # Saving information about scenes
            self.scenes = scenes
            
            # Updating statistics
            self.statistics.total_files = len(files)
            self.statistics.total_size = sum(f.size for f in files)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in prepare_copy_session: {e}", exc_info=True)
            self.error_signal.emit(f"Error preparing copy session: {str(e)}")
            return False
            
    def update_scene_progress(self, scene: SceneInfo):
        """Updating scene progress"""
        completed = 0
        failed = 0
        total_size = 0
        
        # Collecting statistics about files
        for file in scene.files:
            if file.status == "completed":
                completed += 1
            elif file.status == "error":
                failed += 1
            total_size += file.size
            
            # Sending the updated status of each file
            self.progress_signal.emit({
                "file": file.name,
                "progress": file.progress,
                "scene_id": scene.id,
                "status": file.status,
                "camera_id": file.camera_id
            })
        
        # Sending the overall progress of the scene
        self.progress_signal.emit({
            "scene_progress": {
                "id": scene.id,
                "total_files": len(scene.files),
                "copied_files": completed,
                "failed_files": failed,
                "total_size": total_size
            }
        })
        
    def cleanup_temp_files(self):
        """Cleaning up temporary files"""
        for file_path in self.temp_files:
            try:
                if isinstance(file_path, (str, Path)):
                    path = Path(file_path)
                    if path.exists():
                        path.unlink()
                        logger.info(f"Removed temp file: {path}")
            except Exception as e:
                logger.warning(f"Failed to remove temp file {file_path}: {e}")
        self.temp_files.clear()
        
    def retry_failed(self):
        """Retrying the copy of failed files"""
        if not self.failed_files:
            logger.info("No failed files to retry")
            self.status_signal.emit({
                "status": "info",
                "message": "No failed files to retry"
            })
            return
            
        logger.info(f"Retrying {len(self.failed_files)} failed files")
        self.status_signal.emit({
            "status": "info",
            "message": f"Retrying {len(self.failed_files)} failed files"
        })
        
        # Creating a list of files for retry attempts
        retry_files = self.failed_files.copy()
        self.failed_files.clear()
        
        # Starting the copy in the same thread
        if self.copy_thread and self.copy_thread.is_running:
            logger.warning("Copy session is already running")
            return
            
        self.is_paused = False
        self.is_cancelled = False
        
        # Creating new scenes only from failed files
        scenes = {}  # scene_id -> SceneInfo
        for file, target_dir, scene in retry_files:
            if scene.id not in scenes:
                scenes[scene.id] = SceneInfo(
                    id=scene.id,
                    name=scene.name,
                    created_at=scene.created_at,
                    files=[]
                )
            scenes[scene.id].files.append(file)
            
        self.scenes = list(scenes.values())
        self.statistics = FileStatistics()
        self.statistics.total_files = len(retry_files)
        self.statistics.total_size = sum(f[0].size for f in retry_files)
        
        # Creating and starting the copy thread
        self.copy_thread = CopyThread(self, self.current_session)
        
        # Connecting signals
        self.copy_thread.progress_signal.connect(self.progress_signal)
        self.copy_thread.error_signal.connect(self.error_signal)
        self.copy_thread.status_signal.connect(self.status_signal)
        self.copy_thread.finished_signal.connect(self._on_copy_finished)
        
        # Starting the copy process
        self.copy_thread.start()
        
    def collect_files_info(self, devices):
        """Collecting information about files on all cameras"""
        files_info = {}
        
        for device in devices:
            ip = device["ip"]
            serial_number = device["name"].split("._gopro-web._tcp.local.")[0]
            
            try:
                # Using the documented endpoint /gopro/media/list
                media_url = f"http://{ip}:8080/gopro/media/list"
                response = requests.get(media_url, timeout=10)
                response.raise_for_status()
                
                media_list = response.json().get("media", [])
                files_info[serial_number] = {
                    'ip': ip,
                    'total_files': 0,
                    'files': [],
                    'size': 0,
                    'has_jpg': False,
                    'has_gpr': False,
                    'file_counts': {'MP4': 0, 'JPG': 0, 'GPR': 0}
                }
                
                # Processing each directory and files
                for media in media_list:
                    directory = media.get('d', '')
                    
                    for file in media.get('fs', []):
                        file_name = file.get('n', '').upper()
                        # Adding the serial number prefix to the file name
                        prefixed_name = f"{serial_number}_{file_name}"
                        created_time = datetime.fromtimestamp(int(file.get('cre', 0)))
                        size = int(file.get('s', 0))
                        group_id = file.get('g')
                        file_type = file.get('t', '')  # Getting the file type
                        
                        # Checking if the file is part of a sequence
                        if file_type == 'b' and 'b' in file and 'l' in file:
                            # This is a sequence of photos or videos
                            start_num = int(file['b'])
                            end_num = int(file['l'])
                            missing_numbers = file.get('m', [])
                            
                            # Getting the letter code of the group from the file name
                            group_letters = file_name[2:4] if not file_name.startswith('GX') else None
                            
                            # Generating a list of all files in the group
                            for i in range(start_num, end_num + 1):
                                if i not in missing_numbers:
                                    if group_letters:
                                        original_name = f"GP{group_letters}{i:04d}.JPG"
                                        seq_file_name = f"{serial_number}_{original_name}"  # Adding prefix
                                    else:
                                        original_name = f"GX{i:06d}.MP4"
                                        seq_file_name = f"{serial_number}_{original_name}"  # Adding prefix
                                        
                                    file_url = f"http://{camera_ip}:8080/videos/DCIM/{directory}/{original_name}"  # Use the original name for the URL
                                    
                                    logger.info(f"Adding sequence file: {seq_file_name}")
                                    
                                    file_info = {
                                        'name': seq_file_name,  # Using a name with a prefix
                                        'original_name': original_name,  # Keeping the original name.
                                        'folder': directory,
                                        'size': size,
                                        'time': created_time,
                                        'type': 'JPG' if group_letters else 'MP4',
                                        'group_id': group_id,
                                        'is_sequence': True,
                                        'url': file_url
                                    }
                                    files_info[serial_number]['files'].append(file_info)
                                    files_info[serial_number]['total_files'] += 1
                                    files_info[serial_number]['size'] += size
                                    files_info[serial_number]['file_counts']['JPG' if group_letters else 'MP4'] += 1
                                    
                        else:
                            # Standard file (MP4 or single photo)
                            if file_name.endswith('.MP4'):
                                file_type = 'MP4'
                            elif file_name.endswith('.JPG'):
                                file_type = 'JPG'
                                files_info[serial_number]['has_jpg'] = True
                            else:
                                continue
                            
                            file_info = {
                                'name': prefixed_name,  # Using a name with a prefix.
                                'folder': directory,
                                'size': size,
                                'time': created_time,
                                'type': file_type,
                                'group_id': group_id,
                                'is_sequence': False
                            }
                            files_info[serial_number]['files'].append(file_info)
                            files_info[serial_number]['total_files'] += 1
                            files_info[serial_number]['size'] += size
                            files_info[serial_number]['file_counts'][file_type] += 1
                            
                logger.info(f"Found {files_info[serial_number]['total_files']} files on camera {ip}")
                
            except requests.exceptions.Timeout:
                logger.error(f"Failed to get media list from camera {ip}: Connection timeout")
            except Exception as e:
                logger.error(f"Failed to get media list from camera {ip}: {e}")
                
        return files_info
        
    def get_camera_ip(self, camera_id: str) -> str:
        """Obtain the camera's IP address from its ID."""
        return self.camera_ips.get(camera_id, '')
        
class RetryManager:
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 5  # Initial delay in seconds.
        self.failed_files = {}  # {file_id: {attempts: int, last_try: timestamp}}
        self.max_concurrent = 5  # Maximum concurrent connections to a single camera
        self.active_connections = {}  # {camera_ip: current_connections}
        
    def can_retry(self, file_info):
        file_id = f"{file_info.camera_id}_{file_info.name}"
        if file_id not in self.failed_files:
            return True
            
        file_data = self.failed_files[file_id]
        if file_data['attempts'] >= self.max_retries:
            return False
            
        # Checking the time of the last attempt.
        time_since_last = time.time() - file_data['last_try']
        required_delay = self.retry_delay * (2 ** (file_data['attempts'] - 1))
        return time_since_last >= required_delay
        
    def register_attempt(self, file_info, success):
        file_id = f"{file_info.camera_id}_{file_info.name}"
        if success:
            if file_id in self.failed_files:
                del self.failed_files[file_id]
        else:
            if file_id not in self.failed_files:
                self.failed_files[file_id] = {'attempts': 0, 'last_try': 0}
            self.failed_files[file_id]['attempts'] += 1
            self.failed_files[file_id]['last_try'] = time.time()
        