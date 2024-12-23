# Copyright (c) 2024 Andrii Shramko
# Contact: zmei116@gmail.com
# LinkedIn: https://www.linkedin.com/in/andrii-shramko/
# Tags: #ShramkoVR #ShramkoCamera #ShramkoSoft
# License: This code is free to use for non-commercial projects.
# For commercial use, please contact Andrii Shramko at the above email or LinkedIn.

import requests
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Thread
from utils import get_app_root, get_data_dir, setup_logging, check_dependencies
import sys

# Инициализируем логирование
setup_logging()

def check_stop_record_dependencies():
    """Проверка специфических зависимостей для stop_record"""
    required_files = [
        'data/camera_cache.json',
        'utils.py'
    ]
    
    missing_files = []
    app_root = get_app_root()
    
    for file in required_files:
        if not (app_root / file).exists():
            missing_files.append(file)
    
    if missing_files:
        raise FileNotFoundError(f"Missing required files: {', '.join(missing_files)}")

def check_camera_connection(camera_ip, timeout=2):
    """Проверка доступности камеры перед остановкой записи"""
    try:
        response = requests.get(f"http://{camera_ip}:8080/gopro/camera/state", timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False

def stop_recording_synchronized(devices):
    """Синхронная остановка записи на всех камерах"""
    barrier = Barrier(len(devices))
    results = []

    def stop_camera(camera_ip):
        try:
            if not check_camera_connection(camera_ip):
                logging.error(f"Camera {camera_ip} is not accessible")
                return False

            logging.info(f"Camera {camera_ip} waiting for synchronized stop")
            barrier.wait()  # Ждем, пока все камеры будут готовы

            start_time = time.time()
            response = requests.get(f"http://{camera_ip}:8080/gopro/camera/shutter/stop", timeout=5)
            end_time = time.time()

            if response.status_code == 200:
                logging.info(f"Camera {camera_ip} stopped at {start_time:.6f}, response at {end_time:.6f}")
                return True
            else:
                logging.error(f"Failed to stop camera {camera_ip}. Status: {response.status_code}")
                return False
        except Exception as e:
            logging.error(f"Error stopping camera {camera_ip}: {e}")
            return False

    # Запускаем потоки для каждой камеры
    threads = []
    for device in devices:
        thread = Thread(target=lambda: results.append((device['ip'], stop_camera(device['ip']))))
        threads.append(thread)
        thread.start()

    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()

    # Проверяем результаты
    success = all(success for _, success in results)
    if success:
        logging.info("All cameras stopped successfully")
    else:
        failed_cameras = [ip for ip, success in results if not success]
        logging.error(f"Failed to stop cameras: {failed_cameras}")

    return success

def load_devices_from_cache(cache_filename="camera_cache.json"):
    """Загрузка списка камер из кэша с поддержкой портативности"""
    cache_paths = [
        get_data_dir() / cache_filename,  # Основной путь
        get_app_root() / 'data' / cache_filename,  # Альтернативный путь
        get_app_root() / cache_filename  # Запасной путь
    ]
    
    for cache_file in cache_paths:
        try:
            if cache_file.exists():
                with open(cache_file, "r") as file:
                    devices = json.load(file)
                    logging.info(f"Loaded camera cache from {cache_file}")
                    return devices
        except Exception as e:
            logging.warning(f"Failed to load camera cache from {cache_file}: {e}")
            continue
    
    logging.error("No valid camera cache found")
    return None

def main():
    try:
        # Проверяем зависимости перед запуском
        check_dependencies()
        check_stop_record_dependencies()
        
        devices = load_devices_from_cache()
        if not devices:
            logging.error("Camera cache not found or empty. Cannot stop recording.")
            return False

        logging.info("Loaded cached camera devices:")
        for device in devices:
            logging.info(f"Name: {device['name']}, IP: {device['ip']}")

        logging.info("Stopping recording on all cameras...")
        return stop_recording_synchronized(devices)

    except Exception as e:
        logging.error(f"An error occurred in main execution: {e}")
        if getattr(sys, 'frozen', False):
            from PyQt5.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Ошибка при остановке записи")
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Ошибка")
            msg.exec_()
        raise

if __name__ == "__main__":
    main()
