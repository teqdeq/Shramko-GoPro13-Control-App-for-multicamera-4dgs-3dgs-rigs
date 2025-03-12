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

# Настройки по режимам
MODE_SETTINGS = {
    'VIDEO': {
        2: 'Resolution',
        3: 'FPS',
        4: 'FOV',
        5: 'Low Light',
        6: 'Video Format',
        64: 'Video Bitrate',
        65: 'Video Codec',
        66: 'Video EIS',
        67: 'Video Performance Mode',
        75: 'Max Lens Mode',
        83: 'Video Timer',
        84: 'Video Duration',
        85: 'Video Speed',
        86: 'Video Speed Mode',
        88: 'Video Zoom',
        91: 'Video Lens',
        103: 'Video Mode',
        105: 'Video Hindsight',
        106: 'Video Schedule Capture',
        111: 'Video Digital Lens',
        112: 'Video Protune',
        114: 'Video White Balance',
        115: 'Video Color',
        116: 'Video ISO Max',
        117: 'Video ISO Min',
        118: 'Video Shutter',
        121: 'Video EV Comp',
        122: 'Video Sharpness',
        126: 'System Video Mode',
        180: 'Extended System Video Mode'
    },
    'PHOTO': {
        # Общие настройки для всех фото режимов
        130: 'Photo Lens',
        131: 'Photo Protune',
        132: 'Photo White Balance',
        134: 'Photo ISO Max',
        135: 'Photo ISO Min',
        139: 'Photo EV Comp',
        145: 'Photo Sharpness',
        146: 'Photo Color',
        147: 'Photo Digital Lens',
        148: 'Photo Zoom',
        # Single Photo настройки (ID: 69/0)
        69: {
            'name': 'Photo Mode Settings',
            'submode': 0,  # Single Photo
            'settings': {
                125: 'Photo Output',  # RAW/Standard
                154: 'Photo Format',
                156: 'Photo SuperPhoto',
                157: 'Photo HDR',
                158: 'Photo Schedule Capture',
                161: 'Photo Bit Depth',
                162: 'Photo RAW'
            }
        },
        # Night Photo настройки (ID: 69/1)
        70: {
            'name': 'Night Photo Settings',
            'submode': 1,  # Night Photo
            'settings': {
                153: 'Photo Shutter',
                159: 'Photo Night Mode',
                163: 'Photo Night RAW'
            }
        },
        # Burst Photo настройки (ID: 69/2)
        71: {
            'name': 'Burst Photo Settings',
            'submode': 2,  # Burst
            'settings': {
                129: 'Burst Rate'
            }
        },
        # LiveBurst настройки (ID: 69/3)
        72: {
            'name': 'LiveBurst Settings',
            'submode': 3,  # LiveBurst
            'settings': {
                129: 'LiveBurst Rate'
            }
        }
    },
    'TIMELAPSE': {
        167: 'Timelapse Mode',
        168: 'Timelapse Interval',
        173: 'Timelapse Duration'
    }
}

# Настройки режимов фото
PHOTO_MODES = {
    89: {  # Photo SubMode
        'name': 'Photo SubMode',
        'values': {
            0: 'SINGLE',      # Single Photo
            1: 'NIGHT',       # Night Photo
            2: 'BURST',       # Burst Photo
            3: 'LIVEBURST'    # LiveBurst
        }
    }
}

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

async def verify_setting_applied(session, camera_ip, setting_id, expected_value, max_retries=3):
    """Проверка успешности применения настройки"""
    for _ in range(max_retries):
        try:
            url = f"http://{camera_ip}:8080/gp/gpControl/status"
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    state = await response.json()
                    current_value = state.get('settings', {}).get(str(setting_id))
                    if str(current_value) == str(expected_value):
                        return True
                await asyncio.sleep(0.5)
        except Exception as e:
            logging.error(f"Error verifying setting {setting_id}: {e}")
    return False

async def apply_single_setting(session, camera_ip, setting_id, value):
    """Применение одной настройки к камере"""
    try:
        url = f"http://{camera_ip}:8080/gp/gpControl/setting/{setting_id}/{value}"
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                # Проверяем успешность применения
                if await verify_setting_applied(session, camera_ip, setting_id, value):
                    logging.info(f"Successfully applied setting {setting_id}={value} to camera {camera_ip}")
                    return True
                else:
                    logging.warning(f"Failed to verify setting {setting_id}={value} on camera {camera_ip}")
            else:
                logging.error(f"Failed to apply setting {setting_id}={value} to camera {camera_ip}")
            return False
    except Exception as e:
        logging.error(f"Error applying setting {setting_id}: {e}")
        return False

async def apply_settings_batch(session, camera_ip, settings_batch):
    """Применение группы настроек к камере"""
    results = []
    for setting_id, value in settings_batch:
        success = await apply_single_setting(session, camera_ip, setting_id, value)
        results.append((setting_id, success))
        await asyncio.sleep(0.1)  # Уменьшенная пауза между настройками
    return results

async def apply_settings_to_cameras(cameras, settings):
    """Параллельное применение настроек ко всем камерам"""
    async with aiohttp.ClientSession() as session:
        # Преобразуем настройки в список кортежей для удобства обработки
        settings_list = [(int(k), v) for k, v in settings.items() 
                        if int(k) not in READ_ONLY_SETTINGS]
        
        # Разбиваем настройки на группы по 5 штук
        batch_size = 5
        settings_batches = [settings_list[i:i + batch_size] 
                          for i in range(0, len(settings_list), batch_size)]
        
        # Применяем каждую группу настроек параллельно ко всем камерам
        for batch_num, settings_batch in enumerate(settings_batches, 1):
            logging.info(f"\nApplying settings batch {batch_num}/{len(settings_batches)}")
            
            tasks = []
            for camera in cameras:
                task = apply_settings_batch(session, camera['ip'], settings_batch)
                tasks.append(task)
            
            # Ждем завершения применения текущей группы настроек
            batch_results = await asyncio.gather(*tasks)
            
            # Анализируем результаты
            for camera_idx, camera_results in enumerate(batch_results):
                failed_settings = [setting_id for setting_id, success in camera_results if not success]
                if failed_settings:
                    logging.warning(f"Failed settings for camera {cameras[camera_idx]['ip']}: {failed_settings}")
            
            # Уменьшенная пауза между группами настроек
            await asyncio.sleep(0.1)

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
            
            # Проверяем модели всех камер
            target_cameras = []
            for device in devices[1:]:  # Пропускаем первую камеру
                target_model, target_firmware = await get_camera_info_async(session, device['ip'])
                if target_model != model:
                    logging.warning(f"[ASYNC] Target camera model ({target_model}) differs from source ({model})")
                target_cameras.append(device)
                
            if target_cameras:
                logging.info(f"[ASYNC] Starting parallel settings application to {len(target_cameras)} cameras")
                # Применяем настройки ко всем камерам
                await apply_settings_to_cameras(target_cameras, settings)
                logging.info("[ASYNC] Settings application completed!")
            else:
                logging.warning("[ASYNC] No target cameras found to apply settings to!")
        
    except Exception as e:
        logging.error(f"[ASYNC] Error in main: {e}")

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