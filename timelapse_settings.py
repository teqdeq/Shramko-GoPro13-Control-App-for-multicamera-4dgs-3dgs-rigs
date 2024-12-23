# Copyright (c) 2024 Andrii Shramko
# Contact: zmei116@gmail.com
# LinkedIn: https://www.linkedin.com/in/andrii-shramko/
# Tags: #ShramkoVR #ShramkoCamera #ShramkoSoft
# License: This code is free to use for non-commercial projects.
# For commercial use, please contact Andrii Shramko at the above email or LinkedIn.

import requests
import logging
import json
from utils import setup_logging, check_dependencies, get_data_dir
from goprolist_and_start_usb import discover_gopro_devices

# Инициализируем логирование с именем модуля
logger = setup_logging(__name__)

class TimelapseSettings:
    def __init__(self):
        self.settings = {
            'media_format': {'setting': 128, 'option': 13},  # Time Lapse Video
            'interval': {'setting': 5, 'option': 1},         # 1 секунда
            'lens': {'setting': 123, 'option': 101},         # Wide
            'resolution': {'setting': 2, 'option': 1}        # 4K
        }
        
    def apply_settings(self, camera_ip):
        """Применение настроек таймлапс"""
        try:
            for setting_name, setting_data in self.settings.items():
                response = requests.get(
                    f"http://{camera_ip}:8080/gopro/camera/setting?setting={setting_data['setting']}&option={setting_data['option']}", 
                    timeout=5
                )
                if response.status_code != 200:
                    logger.error(f"Failed to set {setting_name} for camera {camera_ip}. Status: {response.status_code}")
                    return False
                logger.info(f"{setting_name} set successfully for camera {camera_ip}")
            return True
        except Exception as e:
            logger.error(f"Error applying timelapse settings for camera {camera_ip}: {e}")
            return False

    def save_settings(self, filename="timelapse_settings.json"):
        """Сохранение настроек в файл"""
        try:
            settings_file = get_data_dir() / filename
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            logger.info(f"Timelapse settings saved to {settings_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving timelapse settings: {e}")
            return False

    def load_settings(self, filename="timelapse_settings.json"):
        """За��рузка настроек из файла"""
        try:
            settings_file = get_data_dir() / filename
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    self.settings = json.load(f)
                logger.info(f"Timelapse settings loaded from {settings_file}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading timelapse settings: {e}")
            return False

def main():
    """Основная функция для запуска из GUI или командной строки"""
    try:
        check_dependencies()
        devices = discover_gopro_devices()
        if not devices:
            logger.error("No GoPro devices found")
            return False

        timelapse_settings = TimelapseSettings()
        timelapse_settings.load_settings()  # Загружаем сохраненные настройки, если есть

        success = True
        for device in devices:
            if not timelapse_settings.apply_settings(device['ip']):
                success = False
                logger.error(f"Failed to apply timelapse settings for {device['name']}")
            else:
                logger.info(f"Timelapse settings applied for {device['name']}")
        
        return success

    except Exception as e:
        logger.error(f"Error in timelapse_settings: {e}")
        return False

if __name__ == "__main__":
    main() 