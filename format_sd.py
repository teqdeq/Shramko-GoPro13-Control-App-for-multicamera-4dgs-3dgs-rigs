# Copyright (c) 2024 Andrii Shramko
# Contact: zmei116@gmail.com
# LinkedIn: https://www.linkedin.com/in/andrii-shramko/
# Tags: #ShramkoVR #ShramkoCamera #ShramkoSoft
# License: This code is free to use for non-commercial projects.
# For commercial use, please contact Andrii Shramko at the above email or LinkedIn.

import requests
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from utils import setup_logging, get_data_dir

# Инициализируем логирование
setup_logging()

def format_camera_sd(camera_ip):
    """Форматирование SD карты для одной камеры"""
    try:
        response = requests.get(f"http://{camera_ip}/gp/gpControl/command/storage/delete/all")
        if response.status_code == 200:
            logging.info(f"SD card formatted successfully for camera {camera_ip}")
            return True
        else:
            logging.error(f"Failed to format SD card for camera {camera_ip}. Status Code: {response.status_code}")
            logging.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error formatting SD card for camera {camera_ip}: {e}")
        return False

def main():
    """Основная функция для форматирования SD карт всех камер"""
    try:
        # Загружаем список камер из кэша
        cache_file = get_data_dir() / "camera_cache.json"
        try:
            with open(cache_file, "r") as f:
                devices = json.load(f)
            logging.info("Loaded cached camera devices:")
            for device in devices:
                logging.info(f"Name: {device['name']}, IP: {device['ip']}")
        except FileNotFoundError:
            logging.error("Camera cache not found. Cannot format SD cards.")
            return False

        # Форматируем SD карты всех камер параллельно
        logging.info("Formatting SD cards on all cameras...")
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(lambda d: format_camera_sd(d["ip"]), devices))
        
        success = all(results)
        if success:
            logging.info("All SD cards formatted successfully")
        else:
            logging.error("Some SD cards failed to format")
        return success

    except Exception as e:
        logging.error(f"Error in format operation: {e}")
        return False

if __name__ == "__main__":
    main()
