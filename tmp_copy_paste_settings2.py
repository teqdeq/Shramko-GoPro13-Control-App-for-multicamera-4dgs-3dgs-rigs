import requests
import logging
import time
from goprolist_and_start_usb import discover_gopro_devices
import asyncio
import aiohttp
from datetime import datetime

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Настройки RAW
RAW_SETTINGS = {
    125: {  # Photo Output
        'name': 'Photo Output',
        'values': {
            0: 'Standard',
            1: 'RAW'
        }
    }
}

# Список настроек только для чтения (read-only)
READ_ONLY_SETTINGS = {13, 31, 37, 41, 42, 43, 44, 45, 76, 87, 102, 123, 124, 128, 144, 149, 155, 160, 164, 165, 166, 169}

# Функция для получения текущего времени с миллисекундами
def get_current_time():
    return datetime.now().strftime('%H:%M:%S.%f')[:-3]

async def get_camera_info_async(session, camera_ip):
    """Асинхронное получение информации о модели камеры"""
    try:
        url = f"http://{camera_ip}:8080/gp/gpControl/info"
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                info = await response.json()
                model = info.get('info', {}).get('model_name')
                firmware = info.get('info', {}).get('firmware_version')
                logging.info(f"Camera model: {model}, Firmware: {firmware}")
                return model, firmware
    except Exception as e:
        logging.error(f"Error getting camera info: {e}")
    return None, None

async def get_camera_settings_async(session, camera_ip):
    """Асинхронное получение всех настроек камеры"""
    try:
        url = f"http://{camera_ip}:8080/gp/gpControl/status"
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                state = await response.json()
                settings = state.get('settings', {})
                if settings:
                    # Получаем текущее значение RAW
                    raw_value = settings.get('125', None)
                    if raw_value is not None:
                        logging.info(f"Current RAW setting (125): {raw_value} ({RAW_SETTINGS[125]['values'].get(raw_value, 'Unknown')})")
                    else:
                        logging.warning("RAW setting not found in camera state")

                    # Получаем остальные настройки
                    writable_settings = {k: v for k, v in settings.items() if int(k) not in READ_ONLY_SETTINGS}
                    logging.info(f"Got {len(writable_settings)} writable settings from camera")
                    return writable_settings
                else:
                    logging.warning("No settings found in camera state")
            else:
                logging.error(f"Failed to get camera state: {response.status}")
    except Exception as e:
        logging.error(f"Error getting settings: {e}")
    return None

async def apply_setting_to_camera_async(session, camera, setting_id, value):
    """Асинхронное применение настройки к камере"""
    try:
        url = f"http://{camera['ip']}:8080/gp/gpControl/setting/{setting_id}/{value}"
        logging.info(f"[ASYNC] Sending setting {setting_id} to camera {camera['name']} at {get_current_time()}")
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                if setting_id in RAW_SETTINGS:
                    raw_info = RAW_SETTINGS[setting_id]
                    value_name = raw_info['values'].get(value, f"Unknown ({value})")
                    logging.info(f"[ASYNC] Applied setting {setting_id} ({raw_info['name']}): {value} ({value_name}) to camera {camera['name']} at {get_current_time()}")
                else:
                    logging.info(f"[ASYNC] Applied setting {setting_id}: {value} to camera {camera['name']} at {get_current_time()}")
            else:
                if setting_id in RAW_SETTINGS:
                    raw_info = RAW_SETTINGS[setting_id]
                    value_name = raw_info['values'].get(value, f"Unknown ({value})")
                    logging.warning(f"[ASYNC] Failed to apply setting {setting_id} ({raw_info['name']}): {value} ({value_name}) to camera {camera['name']} (Status: {response.status}) at {get_current_time()}")
                else:
                    logging.warning(f"[ASYNC] Failed to apply setting {setting_id}: {value} to camera {camera['name']} (Status: {response.status}) at {get_current_time()}")
    except Exception as e:
        logging.error(f"[ASYNC] Error applying setting {setting_id} to camera {camera['name']}: {e} at {get_current_time()}")

async def apply_camera_settings_async(target_cameras, settings):
    """Асинхронное применение настроек ко всем камерам"""
    try:
        # Преобразуем все ключи в целые числа и сортируем
        sorted_settings = sorted([(int(k), v) for k, v in settings.items()])
        
        async with aiohttp.ClientSession() as session:
            # Для каждой настройки
            for setting_id, value in sorted_settings:
                if setting_id in READ_ONLY_SETTINGS:
                    continue
                
                logging.info(f"[ASYNC] Starting parallel apply of setting {setting_id} to {len(target_cameras)} cameras at {get_current_time()}")
                
                # Создаем задачи для всех камер
                tasks = []
                for camera in target_cameras:
                    task = apply_setting_to_camera_async(session, camera, setting_id, value)
                    tasks.append(task)
                
                # Запускаем все задачи одновременно
                await asyncio.gather(*tasks)
                
                logging.info(f"[ASYNC] Completed parallel apply of setting {setting_id} at {get_current_time()}")
                
                # Пауза перед следующей настройкой
                await asyncio.sleep(0.5)
                
    except Exception as e:
        logging.error(f"[ASYNC] Error applying settings: {e} at {get_current_time()}")

async def main_async(devices):
    try:
        if not devices:
            logging.error("[ASYNC] No cameras found")
            return
            
        async with aiohttp.ClientSession() as session:
            # Получаем настройки с первой камеры
            source_camera = devices[0]
            logging.info(f"[ASYNC] Copying settings from camera: {source_camera['name']}")
            
            # Получаем информацию о модели камеры
            model, firmware = await get_camera_info_async(session, source_camera['ip'])
            if not model:
                logging.error("[ASYNC] Failed to get camera info")
                return
                
            # Получаем все настройки
            settings = await get_camera_settings_async(session, source_camera['ip'])
            if not settings:
                logging.error("[ASYNC] Failed to get settings")
                return
                
            logging.info(f"[ASYNC] All {len(settings)} writable settings copied successfully!")
            
            # Ждем 2 секунды
            await asyncio.sleep(2)
            
            # Проверяем модели всех камер
            target_cameras = []
            for device in devices:  # Теперь берем ВСЕ камеры
                target_model, target_firmware = await get_camera_info_async(session, device['ip'])
                if target_model != model:
                    logging.warning(f"[ASYNC] Target camera model ({target_model}) differs from source ({model})")
                target_cameras.append(device)
                
            if target_cameras:
                logging.info(f"[ASYNC] Starting parallel settings application to {len(target_cameras)} cameras at {get_current_time()}")
                # Применяем настройки ко всем камерам одновременно
                await apply_camera_settings_async(target_cameras, settings)
                logging.info(f"[ASYNC] Settings applied to all cameras at {get_current_time()}!")
            else:
                logging.warning("[ASYNC] No target cameras found to apply settings to!")
        
    except Exception as e:
        logging.error(f"[ASYNC] Error in main: {e} at {get_current_time()}")

def main():
    try:
        logging.info(f"[ASYNC] Starting program at {get_current_time()}")
        
        # Ищем камеры только один раз
        logging.info("Discovering cameras...")
        devices = discover_gopro_devices()
        logging.info(f"Found devices: {devices}")
        
        if not devices:
            logging.error("No cameras found")
            return
            
        # Проверяем структуру устройств
        for device in devices:
            logging.info(f"Device: {device}")
            
        # Запускаем асинхронный код, передавая найденные устройства
        asyncio.run(main_async(devices))
        
    except Exception as e:
        logging.error(f"Error in main: {e}", exc_info=True)

if __name__ == "__main__":
    main() 