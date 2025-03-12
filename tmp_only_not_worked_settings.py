import asyncio
import aiohttp
import logging
from goprolist_and_start_usb import discover_gopro_devices
from prime_camera_sn import serial_number as prime_camera_sn

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Список неработающих настроек с их зависимостями
FAILED_SETTINGS = [
    # Сначала применяем базовые настройки режима
    {"id": 126, "value": 0, "name": "System Video Mode", "description": "Highest Quality"},
    {"id": 128, "value": 13, "name": "Media Format", "description": "Time Lapse Video"},
    
    # Настройки видео
    {"id": 41, "value": 100, "name": "Video Resolution", "description": "5.3K"},
    {"id": 42, "value": 6, "name": "Frame Rate", "description": "50.0"},
    {"id": 43, "value": 0, "name": "Webcam Digital Lenses", "description": "Wide"},
    {"id": 44, "value": 9, "name": "Video Resolution", "description": "1080p"},
    {"id": 45, "value": 30, "name": "Video Timelapse Rate", "description": "30 Seconds"},
    {"id": 48, "value": 3, "name": "Video Lens", "description": "Superview"},
    {"id": 144, "value": 9, "name": "Video Resolution", "description": "1080p"},
    
    # Настройки фото
    {"id": 19, "value": 0, "name": "Photo Mode", "description": "SuperPhoto"},
    {"id": 24, "value": 0, "name": "Video Bit Rate", "description": "Standard"},
    {"id": 31, "value": 0, "name": "Photo Interval Duration", "description": "Off"},
    {"id": 37, "value": 0, "name": "Photo Single Interval", "description": "Off"},
    {"id": 75, "value": 0, "name": "Photo Output", "description": "Standard"},
    {"id": 76, "value": 0, "name": "Photo Mode", "description": "SuperPhoto"},
    {"id": 122, "value": 101, "name": "Photo Lens", "description": "Wide"},
    {"id": 123, "value": 101, "name": "Time Lapse Digital Lenses", "description": "Wide"},
    {"id": 146, "value": 0, "name": "Photo Output", "description": "Standard"},
    {"id": 155, "value": 0, "name": "Photo Mode", "description": "SuperPhoto"},
    {"id": 165, "value": 0, "name": "Photo Mode", "description": "SuperPhoto"},
    {"id": 166, "value": 0, "name": "Easy Night Photo", "description": "Super Photo"},
    {"id": 169, "value": 1, "name": "Controls", "description": "Pro"}
]

async def get_camera_info_async(session, camera_ip):
    """Асинхронное получение информации о модели камеры"""
    try:
        url = f"http://{camera_ip}:8080/gp/gpControl/info"
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                info = await response.json()
                model = info.get('info', {}).get('model_name')
                firmware = info.get('info', {}).get('firmware_version')
                serial = info.get('info', {}).get('serial_number')
                logging.info(f"Camera info: Model={model}, Firmware={firmware}, SN={serial}")
                return model, firmware, serial
    except Exception as e:
        logging.error(f"Error getting camera info: {e}")
    return None, None, None

async def is_prime_camera_async(session, camera_ip):
    """Проверяет, является ли камера основной"""
    try:
        _, _, serial = await get_camera_info_async(session, camera_ip)
        is_prime = prime_camera_sn in str(serial)
        if is_prime:
            logging.info(f"Found prime camera: {camera_ip}")
        return is_prime
    except Exception as e:
        logging.error(f"Error checking if camera is prime: {e}")
        return False

async def verify_setting_applied(session, camera_ip, setting_id, expected_value, max_retries=3):
    """Проверка успешности применения настройки"""
    for _ in range(max_retries):
        try:
            url = f"http://{camera_ip}:8080/gopro/camera/setting?setting={setting_id}"
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    state = await response.json()
                    current_value = state.get('option')
                    if str(current_value) == str(expected_value):
                        return True
                await asyncio.sleep(0.1)
        except Exception as e:
            logging.error(f"Error verifying setting {setting_id}: {e}")
    return False

async def apply_single_setting(session, camera_ip, setting):
    """Применение одной настройки к камере"""
    try:
        setting_id = setting['id']
        value = setting['value']
        url = f"http://{camera_ip}:8080/gopro/camera/setting?setting={setting_id}&option={value}"
        
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                # Проверяем успешность применения
                if await verify_setting_applied(session, camera_ip, setting_id, value):
                    logging.info(f"Successfully applied {setting['name']} ({setting['description']}) (ID: {setting_id}, Value: {value})")
                    return True
                else:
                    logging.error(f"Failed to verify {setting['name']} ({setting['description']}) (ID: {setting_id}, Value: {value})")
            else:
                logging.error(f"Failed to apply {setting['name']} ({setting['description']}) (ID: {setting_id}, Value: {value})")
                if response.status == 403:
                    error_text = await response.text()
                    logging.error(f"Error 403: {error_text}")
            return False
    except Exception as e:
        logging.error(f"Error applying setting {setting['name']} (ID: {setting_id}): {e}")
        return False

async def apply_settings_to_camera(session, camera_ip):
    """Применение всех настроек к камере"""
    success_count = 0
    failed_count = 0
    
    for setting in FAILED_SETTINGS:
        success = await apply_single_setting(session, camera_ip, setting)
        if success:
            success_count += 1
        else:
            failed_count += 1
        await asyncio.sleep(0.3)  # Пауза 0.3 секунды между настройками
    
    total = len(FAILED_SETTINGS)
    success_rate = (success_count / total * 100) if total > 0 else 0
    
    logging.info(f"\nРезультаты применения настроек:")
    logging.info(f"Всего настроек: {total}")
    logging.info(f"Успешно применено: {success_count}")
    logging.info(f"Не удалось применить: {failed_count}")
    logging.info(f"Процент успеха: {success_rate:.2f}%")

async def main_async(devices):
    """Основная асинхронная функция"""
    try:
        if not devices:
            logging.error("No cameras found")
            return
            
        async with aiohttp.ClientSession() as session:
            # Находим все камеры кроме prime
            other_cameras = []
            for device in devices:
                if not await is_prime_camera_async(session, device['ip']):
                    other_cameras.append(device)
            
            if not other_cameras:
                logging.error("No secondary cameras found")
                return
                
            logging.info(f"Found {len(other_cameras)} secondary cameras")
                
            # Применяем настройки к каждой камере
            for camera in other_cameras:
                logging.info(f"\nApplying settings to camera {camera['ip']}")
                await apply_settings_to_camera(session, camera['ip'])
            
    except Exception as e:
        logging.error(f"Error in main: {e}")

def main():
    """Точка входа"""
    try:
        logging.info("Starting settings application test")
        
        # Ищем камеры
        devices = discover_gopro_devices()
        
        if not devices:
            logging.error("No cameras found")
            return
            
        # Запускаем тест
        asyncio.run(main_async(devices))
        
    except KeyboardInterrupt:
        logging.info("Test stopped by user")
    except Exception as e:
        logging.error(f"Error in main: {e}", exc_info=True)

if __name__ == "__main__":
    main() 