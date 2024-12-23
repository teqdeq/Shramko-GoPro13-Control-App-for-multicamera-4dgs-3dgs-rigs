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

from file_manager import FileInfo, SceneInfo, FileStatistics

logger = logging.getLogger(__name__)

class CopyThread(QThread):
    """Поток для копирования файлов"""
    
    # Сигналы для обновления GUI
    progress_signal = pyqtSignal(dict)  # Прогресс копирования
    error_signal = pyqtSignal(str)      # Ошибки
    status_signal = pyqtSignal(dict)    # Статус операций
    finished_signal = pyqtSignal()      # Сигнал завершения
    
    def __init__(self, manager, target_dir):
        super().__init__()
        self.manager = manager
        self.target_dir = target_dir
        self.is_running = False
        
    def run(self):
        """Запуск копирования в отдельном потоке"""
        try:
            self.is_running = True
            self._copy_files(self.target_dir)
        except Exception as e:
            logger.error(f"Error in copy thread: {e}", exc_info=True)
            self.error_signal.emit(f"Copy thread failed: {str(e)}")
        finally:
            self.is_running = False
            self.finished_signal.emit()
            
    def _copy_files(self, target_dir: Path):
        """Внутренний метод для копирования файлов"""
        try:
            self.manager.statistics.start()
            
            # Создаем сцены в GUI
            for scene in self.manager.scenes:
                self.progress_signal.emit({
                    "add_scene": {
                        "id": scene.id,
                        "name": scene.name,
                        "files": scene.files
                    }
                })
            
            # Создаем список всех файлов для копирования
            all_files = []
            for scene in self.manager.scenes:
                scene_dir = target_dir / scene.name
                scene_dir.mkdir(parents=True, exist_ok=True)
                for file in scene.files:
                    file.scene_id = scene.id
                    all_files.append((file, scene_dir, scene))

            total_files = len(all_files)
            completed = 0
            failed = 0

            # Используем ThreadPoolExecutor с максимум 4 потоками
            with ThreadPoolExecutor(max_workers=min(4, total_files)) as executor:
                # Запускаем копирование порциями по 4 файла
                for i in range(0, total_files, 4):
                    if self.manager.is_cancelled:
                        break
                        
                    batch = all_files[i:i + 4]
                    futures = []
                    
                    # Запускаем копирование файлов в текущей порции
                    for file, scene_dir, scene in batch:
                        futures.append(
                            executor.submit(self.copy_file, file, scene_dir, scene)
                        )
                    
                    # Ожидаем завершения текущей порции
                    for future in as_completed(futures):
                        try:
                            success = future.result()
                            if success:
                                completed += 1
                                self.manager.statistics.copied_files += 1
                            else:
                                failed += 1
                                self.manager.statistics.failed_files += 1
                            
                            # Обновляем общий прогресс
                            self.status_signal.emit({
                                "total_files": total_files,
                                "copied_files": completed,
                                "failed_files": failed,
                                "duration": self.manager.statistics.get_duration(),
                                "speed": self.manager.statistics.get_speed()
                            })
                            
                        except Exception as e:
                            logger.error(f"Error in copy task: {e}")
                            failed += 1
                            self.manager.statistics.failed_files += 1
                            self.status_signal.emit({
                                "total_files": total_files,
                                "copied_files": completed,
                                "failed_files": failed,
                                "duration": self.manager.statistics.get_duration(),
                                "speed": self.manager.statistics.get_speed()
                            })

            self.manager.statistics.finish()
            
            # Отправляем финальный статус
            if not self.manager.is_cancelled:
                self.status_signal.emit({
                    "status": "completed",
                    "message": "Copy session completed",
                    "total_files": total_files,
                    "copied_files": completed,
                    "failed_files": failed,
                    "duration": self.manager.statistics.get_duration(),
                    "speed": self.manager.statistics.get_speed()
                })
            
        except Exception as e:
            logger.error(f"Error in copy session: {e}", exc_info=True)
            self.error_signal.emit(f"Copy session failed: {str(e)}")
            self.status_signal.emit({
                "status": "error",
                "message": f"Copy session failed: {str(e)}"
            })

    def check_file_exists(self, file_name: str, camera_id: str, target_dir: Path, expected_size: int) -> bool:
        """Проверяет существование файла с учетом серийного номера камеры"""
        try:
            # Разбиваем имя файла на части
            name_parts = file_name.split('.')
            if len(name_parts) != 2:
                return False
                
            # Проверяем все возможные варианты имени файла
            base_name = name_parts[0]
            extension = name_parts[1]
            
            # Варианты имен файлов для проверки:
            # 1. base_name.extension
            # 2. camera_id_base_name.extension
            possible_names = [
                f"{base_name}.{extension}",
                f"{camera_id}_{base_name}.{extension}"
            ]
            
            for name in possible_names:
                file_path = target_dir / name
                if file_path.exists():
                    actual_size = file_path.stat().st_size
                    if actual_size == expected_size:
                        logger.info(f"Found existing file: {name} with matching size")
                        return True
                    else:
                        logger.warning(f"Found file {name} but size mismatch: expected {expected_size}, got {actual_size}")
                        # Удаляем файл с неправильным размером
                        file_path.unlink()
                        
            return False
            
        except Exception as e:
            logger.error(f"Error checking file existence: {str(e)}")
            return False

    def copy_file(self, file: FileInfo, target_dir: Path, scene: SceneInfo) -> bool:
        """Копирование одного файла"""
        target_path = None
        temp_path = None
        try:
            logger.info(f"Starting copy of file: {file.name}")
            
            # Проверяем отмену
            if self.manager.is_cancelled:
                logger.info(f"Copy of {file.name} cancelled")
                return False
            
            # Создаем имя файла с серийным номером камеры в начале
            file_name_parts = file.name.split('.')
            file_name_with_sn = f"{file.camera_id}_{file_name_parts[0]}.{file_name_parts[1]}"
            
            # Создаем директорию назначения
            target_path = target_dir / file_name_with_sn
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Проверяем существование файла
            if self.check_file_exists(file.name, file.camera_id, target_dir, file.size):
                file.status = "completed"
                file.progress = 100
                self.manager.statistics.copied_size += file.size
                
                # Отправляем обновление в GUI
                self.progress_signal.emit({
                    "file": file.name,
                    "progress": 100,
                    "scene_id": scene.id,
                    "status": "Completed"
                })
                self.manager.update_scene_progress(scene)
                return True
            
            # Создаем временный файл для загрузки
            temp_path = target_dir / f".tmp_{file_name_with_sn}"
            
            # Отправляем начальный статус
            self.progress_signal.emit({
                "file": file.name,
                "progress": 0,
                "scene_id": scene.id,
                "status": "Copying..."
            })
            
            # Настройки для повторных попыток
            max_retries = 3
            current_retry = 0
            retry_delay = 1
            
            while current_retry < max_retries:
                try:
                    # Проверяем отмену
                    if self.manager.is_cancelled:
                        logger.info(f"Copy of {file.name} cancelled")
                        return False
                    
                    # Получаем размер файла
                    head_response = requests.head(file.path, timeout=5)
                    if head_response.status_code != 200:
                        raise Exception(f"File not accessible. Status code: {head_response.status_code}")
                    
                    total_size = int(head_response.headers.get('content-length', 0))
                    if total_size == 0:
                        raise Exception("Content-Length header is missing or zero")
                    
                    # Проверяем соответствие размеров
                    if total_size != file.size:
                        logger.warning(f"Size mismatch for {file_name_with_sn}: API reports {file.size}, header reports {total_size}")
                    
                    # Копируем файл
                    downloaded_size = 0
                    with requests.get(file.path, stream=True, timeout=30) as response:
                        response.raise_for_status()
                        with open(temp_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                # Проверяем паузу
                                while self.manager.is_paused and not self.manager.is_cancelled:
                                    time.sleep(0.1)
                                
                                # Проверяем отмену
                                if self.manager.is_cancelled:
                                    logger.info(f"Copy of {file.name} cancelled")
                                    return False
                                
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)
                                    if total_size > 0:
                                        progress = (downloaded_size / total_size) * 100
                                        file.progress = progress
                                        
                                        # Отправляем обновление в GUI
                                        self.progress_signal.emit({
                                            "file": file.name,
                                            "progress": progress,
                                            "scene_id": scene.id,
                                            "status": "Paused..." if self.manager.is_paused else "Copying..."
                                        })
                                        self.manager.update_scene_progress(scene)
                    
                    # Проверяем размер скопированного файла
                    actual_size = temp_path.stat().st_size
                    if actual_size != total_size:
                        raise ValueError(f"Size mismatch for {file_name_with_sn}: expected {total_size}, got {actual_size}")
                    
                    # Перемещаем временный файл в целевой
                    if target_path.exists():
                        target_path.unlink()  # Удаляем существующий файл если есть
                    temp_path.rename(target_path)
                    
                    file.status = "completed"
                    file.progress = 100
                    self.manager.statistics.copied_size += actual_size
                    
                    # Отправляем финальное обновление прогресса
                    self.progress_signal.emit({
                        "file": file.name,
                        "progress": 100,
                        "scene_id": scene.id,
                        "status": "Completed"
                    })
                    self.manager.update_scene_progress(scene)
                    
                    logger.info(f"Successfully copied file: {file_name_with_sn}")
                    return True
                    
                except (requests.exceptions.Timeout,
                        requests.exceptions.ConnectionError,
                        requests.exceptions.RequestException) as e:
                    current_retry += 1
                    if current_retry < max_retries:
                        logger.warning(f"Attempt {current_retry} failed for {file_name_with_sn}: {str(e)}")
                        # Обновляем статус в GUI
                        self.progress_signal.emit({
                            "file": file.name,
                            "progress": file.progress,
                            "scene_id": scene.id,
                            "status": f"Retry {current_retry}/{max_retries}..."
                        })
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise
            
            raise Exception(f"Failed to copy file after {max_retries} attempts")
            
        except Exception as e:
            logger.error(f"Error copying {file.name}: {str(e)}")
            file.status = "failed"
            file.error_message = str(e)
            
            # Отправляем статус ошибки в GUI
            self.progress_signal.emit({
                "file": file.name,
                "progress": file.progress,
                "scene_id": scene.id,
                "status": f"Error: {str(e)}"
            })
            
            # Удаляем временный файл если он существует
            if temp_path and temp_path.exists():
                temp_path.unlink()
            
            return False
            
class CopyManager(QObject):
    """Менеджер копирования файлов с камер"""
    
    # Сигналы для обновления GUI
    progress_signal = pyqtSignal(dict)  # Прогресс копирования
    error_signal = pyqtSignal(str)      # Ошибки
    status_signal = pyqtSignal(dict)    # Статус операций
    
    def __init__(self, max_workers: int = 4):
        super().__init__()
        self.config = self.load_config()
        self.max_workers = self.config.get("copy_settings", {}).get("max_workers", max_workers)
        self.statistics = FileStatistics()
        self.scenes: List[SceneInfo] = []
        self.current_session: Optional[Path] = None
        self.is_paused = False
        self.is_cancelled = False
        self.failed_files = []  # Список неудачных копирований для повторных попыток
        self.temp_files = []    # Список временных файлов для очистки
        self.progress_file = Path("copy_progress.json")
        
        # Инциализация потока и таймера
        self.copy_thread = None
        
    def load_config(self) -> dict:
        """Загрузка конфигурации"""
        try:
            config_path = Path("config.json")
            if config_path.exists():
                with open(config_path, "r") as f:
                    return json.load(f)
            else:
                # Значения по ум��лчанию
                default_config = {
                    "scene_settings": {
                        "max_interval_seconds": 300
                    },
                    "copy_settings": {
                        "max_workers": 4,
                        "retry_count": 3,
                        "retry_delay": 5
                    }
                }
                # Сохраняем конфиг по умолчанию
                with open(config_path, "w") as f:
                    json.dump(default_config, f, indent=4)
                return default_config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
        
    def start_copy_session(self, target_dir: Path):
        """Запуск процесса копирования"""
        try:
            # Сбрасываем флаги состояния
            self.is_paused = False
            self.is_cancelled = False
            self.failed_files.clear()
            self.temp_files.clear()
            
            if not self.prepare_copy_session(target_dir):
                return
                
            # Создаем и запускаем поток копирования
            self.copy_thread = CopyThread(self, target_dir)
            
            # Подключаем сигналы
            self.copy_thread.progress_signal.connect(self.progress_signal)
            self.copy_thread.error_signal.connect(self.error_signal)
            self.copy_thread.status_signal.connect(self.status_signal)
            self.copy_thread.finished_signal.connect(self._on_copy_finished)
            
            # Запускаем копирование
            self.copy_thread.start()
            
        except Exception as e:
            logger.error(f"Error starting copy: {e}", exc_info=True)
            self.error_signal.emit(f"Failed to start copy: {str(e)}")
            self.status_signal.emit({
                "status": "error",
                "message": f"Failed to start copy: {str(e)}"
            })
            
    def pause(self):
        """Приостановка копирования"""
        self.is_paused = True
        logger.info("Copy session paused")
        self.status_signal.emit({
            "status": "paused",
            "message": "Copy session paused"
        })
        
    def resume(self):
        """Возобновление копирования"""
        self.is_paused = False
        logger.info("Copy session resumed")
        self.status_signal.emit({
            "status": "resumed",
            "message": "Copy session resumed"
        })
        
    def cancel(self):
        """Отмена копирования"""
        self.is_cancelled = True
        logger.info("Copy session cancelled")
        self.status_signal.emit({
            "status": "cancelled",
            "message": "Copy session cancelled"
        })
        
    def _on_copy_finished(self):
        """Обработчик завершения копирования"""
        self.copy_thread = None
        logger.info("Copy session finished")
        
    def __del__(self):
        """Деструктор для очистки веменных файлов"""
        self.cleanup_temp_files() 
        
    def get_camera_media_list(self, camera_ip: str) -> List[Dict]:
        """Получение списка медиафайлов с камеры ерез API"""
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
            
            # Обрабатываем структуру ответа от камеры
            for media in data.get('media', []):
                directory = media.get('d', '')  # Папка с файлами
                files = media.get('fs', [])     # Список файлов в папке
                logger.debug(f"Processing directory: {directory}, files count: {len(files)}")
                
                for file in files:
                    file['d'] = directory  # Добавляем информацию о директории к каждому файлу
                    media_list.append(file)
            
            logger.info(f"Found {len(media_list)} media files on camera {camera_ip}")
            logger.debug(f"Media list: {media_list}")
            
            return media_list
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get media list from camera {camera_ip}: {e}")
            return []
            
    def load_camera_cache(self) -> List[Dict]:
        """Загрузка кэша камер и получение списка файлов"""
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
                    
                # Получаем список файлов для каждой камеры
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
            
    def group_files_into_scenes(self, files: List[FileInfo]) -> List[SceneInfo]:
        """Группировка файлов по сценам"""
        if not files:
            return []
            
        # Получаем интервал из конфига
        max_interval = self.config.get("scene_settings", {}).get("max_interval_seconds", 5)
        logger.info(f"Using scene interval: {max_interval} seconds")
            
        # Сортируем файлы по времени создания
        sorted_files = sorted(files, key=lambda x: x.created_at)
        logger.debug(f"Sorted files timestamps:")
        for f in sorted_files:
            logger.debug(f"File: {f.name}, Created: {f.created_at}")
            
        scenes = []
        current_scene_files = [sorted_files[0]]
        scene_start_time = sorted_files[0].created_at
        last_file_time = sorted_files[0].created_at
        logger.debug(f"Starting new scene with file: {sorted_files[0].name} at {scene_start_time}")
        
        for file in sorted_files[1:]:
            # Сравниваем с последним файлом в текущей сцене
            time_diff = (file.created_at - last_file_time).total_seconds()
            logger.debug(f"Checking file: {file.name}")
            logger.debug(f"Time diff from last file: {time_diff} seconds")
            logger.debug(f"Current file time: {file.created_at}")
            logger.debug(f"Last file time: {last_file_time}")
            
            if time_diff > max_interval:
                # Создаем новую сцену
                scene_id = f"scene_{len(scenes):03d}"
                scene_name = f"Scene_{scene_start_time.strftime('%Y%m%d_%H%M%S')}"
                logger.debug(f"Creating new scene: {scene_name} with {len(current_scene_files)} files")
                scene = SceneInfo(
                    id=scene_id,
                    name=scene_name,
                    created_at=scene_start_time,
                    files=current_scene_files.copy()
                )
                scenes.append(scene)
                
                # Начинаем новую сцену
                current_scene_files = [file]
                scene_start_time = file.created_at
                last_file_time = file.created_at
                logger.debug(f"Starting new scene with file: {file.name} at {scene_start_time}")
            else:
                logger.debug(f"Adding file {file.name} to current scene")
                current_scene_files.append(file)
                last_file_time = file.created_at  # Обновляем время последнего файла
        
        # Добавляем последнюю сцену
        if current_scene_files:
            scene_id = f"scene_{len(scenes):03d}"
            scene_name = f"Scene_{scene_start_time.strftime('%Y%m%d_%H%M%S')}"
            logger.debug(f"Creating final scene: {scene_name} with {len(current_scene_files)} files")
            scene = SceneInfo(
                id=scene_id,
                name=scene_name,
                created_at=scene_start_time,
                files=current_scene_files
            )
            scenes.append(scene)
            
        logger.info(f"Grouped {len(files)} files into {len(scenes)} scenes using {max_interval}s interval")
        for scene in scenes:
            logger.debug(f"Scene {scene.name}:")
            for file in scene.files:
                logger.debug(f"  - {file.name} ({file.created_at})")
                
        return scenes
        
    def prepare_copy_session(self, target_dir: Path) -> bool:
        """Подготовка сессии копирования"""
        try:
            logger.info(f"Preparing copy session to: {target_dir}")
            
            # Создаем директорию если не существует
            target_dir.mkdir(parents=True, exist_ok=True)
            self.current_session = target_dir
            
            # Загружаем информацию о амерах и получаем списки файлов
            cameras = self.load_camera_cache()
            if not cameras:
                logger.error("No cameras found in cache")
                self.error_signal.emit("No cameras found in cache")
                return False
                
            logger.info(f"Found {len(cameras)} cameras in cache")
            
            # Собираем информацию о файлах
            files = []
            for camera in cameras:
                camera_id = camera.get('name', '')
                camera_ip = camera.get('ip', '')
                logger.debug(f"Processing camera: {camera_id} ({camera_ip})")
                
                media_list = camera.get('media', [])
                logger.debug(f"Found {len(media_list)} media files for camera {camera_id}")
                
                for media in media_list:
                    logger.debug(f"Processing media: {media}")
                    
                    # Получаем информацию о файле
                    file_name = media.get('n')
                    directory = media.get('d', '')
                    
                    if not file_name:
                        logger.warning(f"No filename in media info: {media}")
                        continue
                        
                    file_url = f"http://{camera_ip}:8080/videos/DCIM/{directory}/{file_name}"
                    logger.debug(f"Media URL: {file_url}")
                    
                    # Создаем объект FileInfo
                    created_timestamp = int(media.get("cre", 0))
                    logger.debug(f"File: {file_name}, Raw timestamp: {created_timestamp}")
                    created_time = datetime.fromtimestamp(created_timestamp)
                    logger.debug(f"Converted timestamp to: {created_time}")
                    
                    file_info = FileInfo(
                        name=file_name,
                        path=file_url,
                        size=int(media.get("s", 0)),
                        created_at=created_time,
                        camera_id=camera_id
                    )
                    files.append(file_info)
                    logger.debug(f"Added file to copy list: {file_info}, Created at: {file_info.created_at}")
            
            if not files:
                logger.error("No files found to copy")
                self.error_signal.emit("No files found to copy")
                return False
                
            logger.info(f"Found {len(files)} files to copy")
            
            # Группируем файлы по сценам
            self.scenes = self.group_files_into_scenes(files)
            logger.info(f"Grouped files into {len(self.scenes)} scenes")
            
            self.statistics = FileStatistics()
            self.statistics.total_files = len(files)
            self.statistics.total_size = sum(f.size for f in files)
            
            logger.info(f"Total files: {self.statistics.total_files}")
            logger.info(f"Total size: {self.statistics.total_size} bytes")
            
            return True
                
        except Exception as e:
            logger.error(f"Error preparing copy session: {e}", exc_info=True)
            self.error_signal.emit(f"Failed to prepare copy session: {str(e)}")
            return False
            
    def update_scene_progress(self, scene: SceneInfo):
        """Обновление прогресса сцены"""
        completed = sum(1 for f in scene.files if f.status == "completed")
        failed = sum(1 for f in scene.files if f.status == "error")
        total_size = sum(f.size for f in scene.files)
        
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
        """Очистка временных файлов"""
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
        """Повторная попытка копирования неудачных файлов"""
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
        
        # Создаем список файлов для повторной попытки
        retry_files = self.failed_files.copy()
        self.failed_files.clear()
        
        # Запускаем копирование в том же потоке
        if self.copy_thread and self.copy_thread.is_running:
            logger.warning("Copy session is already running")
            return
            
        self.is_paused = False
        self.is_cancelled = False
        
        # Создаем новые сцены только из неудачных файлов
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
        
        # Создаем и запускаем поток копирования
        self.copy_thread = CopyThread(self, self.current_session)
        
        # Подключаем сигналы
        self.copy_thread.progress_signal.connect(self.progress_signal)
        self.copy_thread.error_signal.connect(self.error_signal)
        self.copy_thread.status_signal.connect(self.status_signal)
        self.copy_thread.finished_signal.connect(self._on_copy_finished)
        
        # Запускаем копирование
        self.copy_thread.start()
        