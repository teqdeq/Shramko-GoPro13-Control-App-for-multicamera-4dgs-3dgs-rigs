# Copyright (c) 2024 Andrii Shramko
# Contact: zmei116@gmail.com
# LinkedIn: https://www.linkedin.com/in/andrii-shramko/
# Tags: #ShramkoVR #ShramkoCamera #ShramkoSoft
# License: This code is free to use for non-commercial projects.
# For commercial use, please contact Andrii Shramko at the above email or LinkedIn.

import requests
import logging
from concurrent.futures import ThreadPoolExecutor
from goprolist_and_start_usb import discover_gopro_devices
from utils import get_app_root, setup_logging, check_dependencies

# Инициализируем логирование
setup_logging()

def check_preset_dependencies():
    """Проверка зависимостей для установки пресета"""
    required_files = [
        'data/camera_cache.json',
        'utils.py',
        'goprolist_and_start_usb.py'
    ]
    
    app_root = get_app_root()
    missing_files = []
    
    for file in required_files:
        if not (app_root / file).exists():
            missing_files.append(file)
    
    if missing_files:
        raise FileNotFoundError(f"Missing required files: {', '.join(missing_files)}")

def set_preset(camera_ip):
    """Установка пресета на камеру"""
    try:
        # Возвращаем правильный URL для загрузки пресета
        url = f"http://{camera_ip}:8080/gopro/camera/presets/load?id=0"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            logging.info(f"Preset successfully loaded on camera {camera_ip}")
        else:
            logging.error(f"Failed to load preset on camera {camera_ip}. Status Code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error loading preset on camera {camera_ip}: {e}")

def main():
    """Основная функция для установки пресета на все камеры"""
    try:
        # Проверяем зависимости
        check_dependencies()
        check_preset_dependencies()
        
        # Получаем список камер
        devices = discover_gopro_devices()
        if not devices:
            logging.error("No GoPro devices found")
            return False

        # Устанавливаем пресет на все камеры параллельно
        logging.info("Loading preset on all cameras...")
        with ThreadPoolExecutor() as executor:
            executor.map(lambda d: set_preset(d['ip']), devices)
        
        return True

    except Exception as e:
        logging.error(f"Error in preset operation: {e}")
        return False

if __name__ == "__main__":
    main()
