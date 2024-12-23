# Copyright (c) 2024 Andrii Shramko
# Contact: zmei116@gmail.com
# LinkedIn: https://www.linkedin.com/in/andrii-shramko/
# Tags: #ShramkoVR #ShramkoCamera #ShramkoSoft
# License: This code is free to use for non-commercial projects.
# For commercial use, please contact Andrii Shramko at the above email or LinkedIn.

from goprocam import GoProCamera
from goprocam import constants
import logging
import time
from utils import setup_logging
from goprolist_and_start_usb import discover_gopro_devices

# Инициализируем логирование с именем модуля
logger = setup_logging(__name__)

def take_raw_photo():
    try:
        # Получаем список камер
        devices = discover_gopro_devices()
        if not devices:
            logger.error("No GoPro devices found")
            return False

        for device in devices:
            try:
                ip = device['ip']
                logger.info(f"Connecting to GoPro at {ip}")
                
                # Инициализация камеры с конкретным IP
                gopro = GoProCamera.GoPro(ip_address=ip)
                
                # Проверяем тип камеры
                camera_type = gopro.whichCam()
                logger.info(f"Camera type: {camera_type}")
                
                # Ждем стабилизации соединения
                time.sleep(2)
                
                # Переключаем в режим фото
                gopro.mode(constants.Mode.PhotoMode)
                logger.info("Photo mode set")
                
                # Делаем фото с таймером 2 секунды
                photo_url = gopro.take_photo(timer=2)
                logger.info(f"Photo taken, URL: {photo_url}")
                
                # Скачиваем фото
                if photo_url:
                    gopro.downloadLastMedia(custom_filename=f"RAW_photo_{device['name']}.jpg")
                    logger.info(f"Photo downloaded from {device['name']}")
                
            except Exception as e:
                logger.error(f"Error with camera {device['name']}: {e}")
                continue
        
        return True
        
    except Exception as e:
        logger.error(f"Error in take_raw_photo: {e}")
        return False

if __name__ == "__main__":
    try:
        take_raw_photo()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise 