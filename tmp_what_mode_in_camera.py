import logging
from goprolist_and_start_usb import discover_gopro_devices
import requests
import json
from read_and_write_all_settings_from_prime_to_other_v02 import (
    is_prime_camera, USB_HEADERS, get_camera_status
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_camera_mode():
    """Определяет текущий режим основной камеры"""
    try:
        # Получаем список камер
        cameras = discover_gopro_devices()
        if not cameras:
            logger.error("Камеры не найдены")
            return None

        # Находим основную камеру
        prime_camera = None
        for camera in cameras:
            if is_prime_camera(camera):
                prime_camera = camera
                break

        if not prime_camera:
            logger.error("Основная камера не найдена")
            return None

        logger.info(f"Найдена основная камера: {prime_camera['ip']}")

        # Получаем статус камеры
        url = f"http://{prime_camera['ip']}:8080/gopro/camera/state"
        response = requests.get(url, headers=USB_HEADERS, timeout=5)
        
        if response.status_code != 200:
            logger.error(f"Ошибка получения статуса камеры. Код: {response.status_code}")
            return None

        # Получаем и выводим полный ответ для анализа
        status_data = response.json()
        logger.info("Полный ответ от камеры:")
        logger.info(json.dumps(status_data, indent=2))

        # Проверяем структуру ответа
        if not isinstance(status_data, dict):
            logger.error(f"Неверный формат ответа: {status_data}")
            return None

        # Получаем режим из settings.144
        settings = status_data.get('settings', {})
        if not isinstance(settings, dict):
            logger.error(f"Поле settings не найдено или неверного формата: {status_data}")
            return None

        # Пробуем получить режим из settings.144
        current_mode = settings.get('144')
        logger.info(f"Значение settings.144: {current_mode}")

        # Определяем режим по значению settings.144
        mode_map = {
            12: 'video',      # Режим видео
            16: 'photo',      # Режим фото
            13: 'timelapse'   # Режим таймлапс
        }

        if current_mode in mode_map:
            mode = mode_map[current_mode]
            logger.info(f"Определен режим камеры: {current_mode} -> {mode}")
            return mode
        else:
            logger.warning(f"Неизвестное значение режима: {current_mode}")
            return None

    except Exception as e:
        logger.error(f"Ошибка при определении режима камеры: {e}")
        return None

if __name__ == "__main__":
    print("\nОпределение режима основной камеры...")
    mode = get_camera_mode()
    if mode:
        print(f"\nТекущий режим камеры: {mode}")
    else:
        print("\nНе удалось определить режим камеры") 