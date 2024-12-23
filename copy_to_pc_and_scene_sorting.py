# Copyright (c) 2024 Andrii Shramko
# Contact: zmei116@gmail.com
# LinkedIn: https://www.linkedin.com/in/andrii-shramko/
# Tags: #ShramkoVR #ShramkoCamera #ShramkoSoft
# License: This code is free to use for non-commercial projects.
# For commercial use, please contact Andrii Shramko at the above email or LinkedIn.

import os
import sys
import requests
import logging
from datetime import datetime
from pathlib import Path
from goprolist_and_start_usb import discover_gopro_devices
from prime_camera_sn import serial_number as prime_camera_sn
from utils import get_app_root, setup_logging, check_dependencies

def create_folder_structure_and_copy_files(destination_root, scene_time_threshold=5):
    """
    Копирование и сортировка файлов с камер
    """
    try:
        setup_logging()
        logger = logging.getLogger(__name__)
        check_dependencies()
        
        destination_root = Path(destination_root)
        
        # Проверяем права доступа
        if not os.access(str(destination_root), os.W_OK):
            logger.error(f"No write access to destination directory: {destination_root}")
            return
            
        # Шаг 1: Сбор информации о файлах на камерах
        logger.info("Collecting files information from cameras...")
        devices = discover_gopro_devices()
        if not devices:
            logger.error("No GoPro devices found")
            return
            
        files_info = collect_files_info(devices)
        
        # Шаг 2: Проверка существующих файлов
        logger.info("Checking existing files...")
        existing_files = check_existing_files(destination_root, files_info)
        
        # Шаг 3: Группировка файлов по сценам
        logger.info("Calculating scene ranges...")
        scenes = calculate_scene_time_ranges(files_info, scene_time_threshold)
        
        # Шаг 4: Создание структуры папок
        logger.info("Creating scene folders...")
        scene_folders = create_scene_folders(destination_root, scenes)
        
        # Шаг 5: Копирование файлов
        copied_files = []
        failed_files = []
        
        for scene_folder in scene_folders:
            logger.info(f"Processing scene: {scene_folder['name']}")
            for file in scene_folder['files']:
                # Исправляем URL, добавляем порт 8080
                source_url = f"http://{files_info[file['camera']]['ip']}:8080/videos/DCIM/{file['folder']}/{file['name']}"
                dest_filename = f"{file['camera']}_{file['name']}"
                dest_path = scene_folder['folder'] / dest_filename
                
                logger.info(f"Source URL: {source_url}")  # Добавляем лог URL
                
                # Проверяем существующий файл
                if any(ef['name'] == dest_filename for ef in existing_files.get(file['camera'], [])):
                    logger.info(f"File already exists: {dest_filename}")
                    copied_files.append({'camera': file['camera'], 'file': file['name']})
                    continue
                
                try:
                    logger.info(f"Copying {dest_filename}...")
                    
                    # Проверяем доступность файла перед копированием
                    check_response = requests.head(source_url, timeout=5)
                    if check_response.status_code != 200:
                        raise Exception(f"File not accessible. Status code: {check_response.status_code}")
                    
                    # Получаем размер файла из информации о камере
                    file_info = next(
                        (f for f in files_info[file['camera']]['files'] if f['name'] == file['name']),
                        None
                    )
                    if not file_info:
                        raise Exception("File info not found")
                    
                    success = copy_file_with_verification(
                        source_url, 
                        dest_path, 
                        file_info['size']  # Используем правильный размер файла
                    )
                    
                    if success:
                        copied_files.append({'camera': file['camera'], 'file': file['name']})
                    else:
                        failed_files.append({
                            'camera': file['camera'],
                            'file': file['name'],
                            'reason': 'Copy verification failed'
                        })
                        
                except Exception as e:
                    logger.error(f"Error copying {dest_filename}: {e}")
                    failed_files.append({
                        'camera': file['camera'],
                        'file': file['name'],
                        'reason': str(e)
                    })
        
        # Шаг 6: Проверка результатов
        verification_results = verify_all_files_copied(files_info, copied_files, failed_files)
        
        # Шаг 7: Сохранение лога операции
        log_copy_operation(destination_root, verification_results)
        
        # Возвращаем результаты для GUI
        return {
            'status': 'success' if not failed_files else 'incomplete',
            'verification': verification_results,
            'copied': len(copied_files),
            'failed': len(failed_files),
            'total_scenes': len(scene_folders)
        }

    except Exception as e:
        logger.error(f"Unexpected error during copy operation: {e}", exc_info=True)
        if getattr(sys, 'frozen', False):
            from PyQt5.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Ошибка при копировании файлов")
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Ошибка")
            msg.exec_()
        raise

def verify_all_files_copied(files_info, copied_files, failed_files):
    """Проверка что все файлы были скопированы"""
    verification_results = {}
    
    for serial_number, info in files_info.items():
        if 'error' in info:
            verification_results[serial_number] = {
                'status': 'ERROR',
                'reason': info['error'],
                'missing_files': []
            }
            continue
        
        # Проверяем каждый файл
        missing_files = []
        for file_info in info['files']:
            file_copied = any(
                cf['camera'] == serial_number and cf['file'] == file_info['name']
                for cf in copied_files
            )
            file_failed = any(
                ff['camera'] == serial_number and ff['file'] == file_info['name']
                for ff in failed_files
            )
            
            if not file_copied and not file_failed:
                missing_files.append(file_info['name'])
        
        verification_results[serial_number] = {
            'status': 'OK' if not missing_files else 'INCOMPLETE',
            'total_files': info['total_files'],
            'copied_files': len([cf for cf in copied_files if cf['camera'] == serial_number]),
            'failed_files': len([ff for ff in failed_files if ff['camera'] == serial_number]),
            'missing_files': missing_files
        }
    
    # Выводим результаты проверки
    print("\nVerification Results:")
    print("=" * 50)
    for serial_number, result in verification_results.items():
        print(f"\nCamera {serial_number}:")
        print(f"Status: {result['status']}")
        if result['status'] == 'ERROR':
            print(f"Error: {result['reason']}")
        else:
            print(f"Total files: {result.get('total_files', 0)}")
            print(f"Copied files: {result.get('copied_files', 0)}")
            print(f"Failed files: {result.get('failed_files', 0)}")
            if result.get('missing_files'):
                print("Missing files:")
                for file in result['missing_files']:
                    print(f"  - {file}")
    
    return verification_results

def calculate_scene_time_ranges(files_info, scene_time_threshold=5):
    """Расчет временных диапазонов для сцен"""
    all_files = []
    for serial_number, info in files_info.items():
        if 'error' not in info:
            for file_info in info['files']:
                all_files.append({
                    'camera': serial_number,
                    'time': file_info['time'],
                    'name': file_info['name'],
                    'folder': file_info['folder'],
                    'size': file_info['size']  # Добавляем размер файла
                })
    
    # Сортируем файлы по времени
    all_files.sort(key=lambda x: x['time'])
    
    # Группируем файлы по сценам
    scenes = []
    current_scene = []
    
    for i, file in enumerate(all_files):
        if not current_scene:
            current_scene = [file]
        else:
            # Проверяем временную разницу и принадлежность к одной сцене
            time_diff = abs((file['time'] - current_scene[0]['time']).total_seconds())
            
            # Файлы принадлежат одной сцене если:
            # 1. Разница во времени меньше порога
            # 2. Файлы от разных камер
            if time_diff <= scene_time_threshold and not any(
                cf['camera'] == file['camera'] for cf in current_scene
            ):
                current_scene.append(file)
            else:
                if len(current_scene) > 0:
                    scenes.append(current_scene)
                current_scene = [file]
    
    if current_scene:
        scenes.append(current_scene)
    
    return scenes

def create_scene_folders(destination_root, scenes):
    """Создание структуры папок для сцен"""
    scene_folders = []
    used_timestamps = set()  # Для отслеживания уже использованных временных меток
    
    for scene_index, scene_files in enumerate(scenes, 1):
        # Используем время съемки с основной камеры или первой доступной
        prime_file = next(
            (f for f in scene_files if f['camera'] == prime_camera_sn),
            scene_files[0]
        )
        
        scene_timestamp = prime_file['time'].strftime("%Y_%m_%d_%H_%M_%S")
        
        # Проверяем уникальность временной метки
        if scene_timestamp in used_timestamps:
            continue
        
        used_timestamps.add(scene_timestamp)
        scene_folder_name = f"scene{scene_index:02d}_{scene_timestamp}"
        scene_folder = destination_root / scene_folder_name
        scene_folder.mkdir(exist_ok=True)
        
        scene_folders.append({
            'folder': scene_folder,
            'files': scene_files,
            'name': scene_folder_name,
            'timestamp': scene_timestamp
        })
    
    return scene_folders

def log_copy_operation(destination_root, verification_results):
    """Сохранение лога операции копирования"""
    log_file = destination_root / 'copy_log.txt'
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\nCopy Operation Log - {timestamp}\n")
        f.write("=" * 50 + "\n")
        
        for serial_number, result in verification_results.items():
            f.write(f"\nCamera {serial_number}:\n")
            f.write(f"Status: {result['status']}\n")
            if result['status'] == 'ERROR':
                f.write(f"Error: {result['reason']}\n")
            else:
                f.write(f"Total files: {result.get('total_files', 0)}\n")
                f.write(f"Copied files: {result.get('copied_files', 0)}\n")
                f.write(f"Failed files: {result.get('failed_files', 0)}\n")
                if result.get('missing_files'):
                    f.write("Missing files:\n")
                    for file in result['missing_files']:
                        f.write(f"  - {file}\n")
        
        f.write("\n" + "=" * 50 + "\n")

def collect_files_info(devices):
    """Сбор информации о файлах на всех камерах"""
    files_info = {}
    
    for device in devices:
        ip = device["ip"]
        serial_number = device["name"].split("._gopro-web._tcp.local.")[0]
        
        try:
            # Используем документированный endpoint /gopro/media/list
            media_url = f"http://{ip}:8080/gopro/media/list"
            response = requests.get(media_url, timeout=10)
            response.raise_for_status()
            
            media_list = response.json().get("media", [])
            files_info[serial_number] = {
                'ip': ip,
                'total_files': 0,
                'files': [],
                'size': 0
            }
            
            for media in media_list:
                for file in media.get("fs", []):
                    if file.get("n").upper().endswith(('.MP4', '.JPG')):
                        # Преобразуем строку размера в число
                        file_size = int(file.get("s", "0"))
                        file_info = {
                            'name': file.get("n"),
                            'folder': media.get("d"),
                            'size': file_size,
                            'time': datetime.fromtimestamp(int(file.get("cre")))
                        }
                        files_info[serial_number]['files'].append(file_info)
                        files_info[serial_number]['total_files'] += 1
                        files_info[serial_number]['size'] += file_size  # Теперь складываем числа
            
            logging.info(f"Camera {serial_number}: found {files_info[serial_number]['total_files']} files, "
                        f"{files_info[serial_number]['size'] / (1024*1024):.2f} MB")
                        
        except Exception as e:
            logging.error(f"Error collecting files from camera {serial_number}: {e}")
            files_info[serial_number] = {'error': str(e)}
    
    return files_info

def check_existing_files(destination_root, files_info):
    """Проверка существующих файлов в целевых директориях"""
    existing_files = {}
    
    for serial_number, info in files_info.items():
        if 'error' in info:
            continue
            
        existing_files[serial_number] = []
        
        # Ищем файлы во всех поддиректориях
        for root, _, files in os.walk(destination_root):
            for file_info in info['files']:
                file_name = f"{serial_number}_{file_info['name']}"
                if file_name in files:
                    file_path = os.path.join(root, file_name)
                    existing_files[serial_number].append({
                        'name': file_name,
                        'path': file_path,
                        'size': os.path.getsize(file_path)
                    })
                    logging.info(f"Found existing file: {file_name}")
    
    return existing_files

def copy_file_with_verification(source_url, dest_path, expected_size):
    """Копирование файла с проверкой размера"""
    try:
        # Проверяем доступность файла
        head_response = requests.head(source_url, timeout=5)
        if head_response.status_code != 200:
            raise Exception(f"File not accessible. Status code: {head_response.status_code}")
        
        # Получаем реальный размер файла
        total_size = int(head_response.headers.get('content-length', 0))
        if total_size == 0:
            raise Exception("Content-Length header is missing or zero")
        
        # Проверяем соответствие размеров
        if total_size != expected_size:
            logging.warning(f"Size mismatch for {dest_path.name}: API reports {expected_size}, header reports {total_size}")
        
        # Создаем родительские директории
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Копируем файл
        downloaded_size = 0
        with requests.get(source_url, stream=True, timeout=30) as response:
            response.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            if progress % 5 < 1:
                                logging.info(f"Download progress for {dest_path.name}: {progress:.1f}%")
        
        # Проверяем размер скопированного файла
        actual_size = os.path.getsize(dest_path)
        if actual_size != total_size:
            logging.error(f"Size mismatch for {dest_path.name}: expected {total_size}, got {actual_size}")
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return False
        
        logging.info(f"Successfully copied and verified: {dest_path.name} ({actual_size} bytes)")
        return True
        
    except Exception as e:
        logging.error(f"Error copying {source_url} to {dest_path}: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python copy_to_pc_and_scene_sorting.py <destination_root>")
        sys.exit(1)
    
    destination = sys.argv[1]
    create_folder_structure_and_copy_files(destination)
