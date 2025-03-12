import logging
import json
import aiohttp
import asyncio
from datetime import datetime
import os
from goprolist_and_start_usb import discover_gopro_devices

# Создаем директорию для логов если её нет
os.makedirs('logs', exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/gopro_settings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Статистика применения настроек
STATS = {
    'total_settings': 0,
    'applied_settings': 0,
    'failed_settings': 0,
    'skipped_settings': 0,
    'failed_list': []
}

# Загружаем доступные значения из файла
try:
    with open('all_avalable_gopro10_value_settings.json', 'r') as f:
        AVAILABLE_SETTINGS = json.load(f)
        logger.info(f"Loaded available settings from file: {len(AVAILABLE_SETTINGS['settings'])} settings")
except Exception as e:
    logger.error(f"Failed to load available settings: {str(e)}")
    AVAILABLE_SETTINGS = {'settings': {}}

async def get_camera_status(camera_ip):
    """Получение полного статуса камеры"""
    url = f"http://{camera_ip}:8080/gopro/camera/state"
    try:
        async with aiohttp.ClientSession() as session:
            logger.debug(f"Getting camera status from {url}")
            async with session.get(url) as response:
                status = response.status
                response_text = await response.text()
                logger.debug(f"Status response status: {status}")
                logger.debug(f"Status response body: {response_text}")
                
                if status == 200:
                    data = await response.json()
                    logger.info(f"Got camera status successfully")
                    logger.debug(f"Full camera status: {json.dumps(data, indent=2)}")
                    return data
                else:
                    logger.error(f"Failed to get camera status, status: {status}")
                    return None
                    
    except Exception as e:
        logger.error(f"Error getting camera status: {str(e)}")
        return None

def is_value_supported(setting_id, value):
    """Проверка поддерживается ли значение для настройки"""
    setting_info = AVAILABLE_SETTINGS['settings'].get(str(setting_id))
    if not setting_info:
        logger.warning(f"Setting {setting_id} not found in available settings")
        STATS['skipped_settings'] += 1
        return False
        
    supported_options = setting_info.get('supported_options', [])
    if not supported_options:
        logger.warning(f"No supported options for setting {setting_id}")
        STATS['skipped_settings'] += 1
        return False
        
    supported_values = [opt['id'] for opt in supported_options]
    if value not in supported_values:
        logger.warning(f"Value {value} not in supported values for setting {setting_id}: {supported_values}")
        STATS['skipped_settings'] += 1
        return False
        
    return True

async def apply_setting(camera_ip, setting_id, value):
    """Применение настройки к камере"""
    STATS['total_settings'] += 1
    
    # Проверяем поддерживается ли значение
    if not is_value_supported(setting_id, value):
        return False
    
    url = f"http://{camera_ip}:8080/gopro/camera/setting?setting={setting_id}&option={value}"
    try:
        async with aiohttp.ClientSession() as session:
            logger.debug(f"Sending GET request to {url}")
            async with session.get(url) as response:
                status = response.status
                response_text = await response.text()
                logger.debug(f"Response status: {status}")
                logger.debug(f"Response body: {response_text}")
                
                if status == 200:
                    logger.info(f"Successfully applied setting {setting_id}={value}")
                    STATS['applied_settings'] += 1
                    await asyncio.sleep(0.2)  # Небольшая пауза после успешного применения
                    return True
                else:
                    logger.error(f"Failed to apply setting {setting_id}={value}, status: {status}")
                    STATS['failed_settings'] += 1
                    STATS['failed_list'].append((setting_id, value, status))
                    return False
                    
    except Exception as e:
        logger.error(f"Error applying setting {setting_id}={value}: {str(e)}")
        STATS['failed_settings'] += 1
        STATS['failed_list'].append((setting_id, value, 'error'))
        return False

async def verify_setting(camera_ip, setting_id, expected_value):
    """Проверка что настройка применил��сь корректно"""
    status = await get_camera_status(camera_ip)
    if not status:
        logger.error(f"Failed to verify setting {setting_id} - couldn't get camera status")
        return False
        
    current_value = status.get('settings', {}).get(str(setting_id))
    if current_value == expected_value:
        logger.info(f"Setting {setting_id} verified successfully: {current_value}")
        return True
    else:
        logger.warning(f"Setting {setting_id} verification failed. Expected: {expected_value}, Got: {current_value}")
        return False

def run_discover_gopro_devices():
    """Запуск поиска камер в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        cameras = discover_gopro_devices()
        return cameras
    finally:
        loop.close()

def print_settings_report():
    """Вывод отчета о применении настроек"""
    logger.info("\n=== Settings Application Report ===")
    logger.info(f"Total settings in file: {len(AVAILABLE_SETTINGS['settings'])}")
    logger.info(f"Total settings processed: {STATS['total_settings']}")
    logger.info(f"Successfully applied: {STATS['applied_settings']}")
    logger.info(f"Failed to apply: {STATS['failed_settings']}")
    logger.info(f"Skipped (not supported): {STATS['skipped_settings']}")
    
    if STATS['failed_list']:
        logger.info("\nFailed settings list:")
        for setting_id, value, status in STATS['failed_list']:
            setting_info = AVAILABLE_SETTINGS['settings'].get(str(setting_id), {})
            supported_options = setting_info.get('supported_options', [])
            supported_values = [opt['id'] for opt in supported_options]
            logger.info(f"Setting ID: {setting_id}")
            logger.info(f"Attempted value: {value}")
            logger.info(f"Status code: {status}")
            logger.info(f"Supported values: {supported_values}")
            logger.info("---")
            
    # Добавляем процент успешности
    total_attempted = STATS['applied_settings'] + STATS['failed_settings']
    if total_attempted > 0:
        success_rate = (STATS['applied_settings'] / total_attempted) * 100
        logger.info(f"\nSuccess rate: {success_rate:.2f}%")
    
    # Добавляем сравнение с доступными настройками
    total_available = len(AVAILABLE_SETTINGS['settings'])
    if total_available > 0:
        coverage = (STATS['total_settings'] / total_available) * 100
        logger.info(f"Settings coverage: {coverage:.2f}% ({STATS['total_settings']}/{total_available})")

async def main_async():
    """Основная логика работы с настройками"""
    try:
        # Получение списка камер в отдельном потоке
        loop = asyncio.get_event_loop()
        cameras = await loop.run_in_executor(None, run_discover_gopro_devices)
        
        if not cameras:
            logger.error("No cameras found")
            return

        # Получение настроек с первой камеры
        primary_camera = cameras[0]
        logger.info(f"Using primary camera: {primary_camera['ip']}")
        
        # Получение статуса камеры перед началом работы
        status = await get_camera_status(primary_camera['ip'])
        if not status:
            logger.error("Failed to get camera status")
            return
            
        # Получаем текущие настройки из статуса
        current_settings = status.get('settings', {})
        if not current_settings:
            logger.error("No settings found in camera status")
            return
            
        logger.info(f"Got {len(current_settings)} settings from primary camera")
        
        # Сохранение текущих настроек
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f'camera_settings_{timestamp}.json', 'w') as f:
            json.dump(current_settings, f, indent=2)
            logger.info(f"Saved current settings to camera_settings_{timestamp}.json")

        # Применение настроек к остальным камерам
        for camera in cameras[1:]:
            logger.info(f"Applying settings to camera: {camera['ip']}")
            
            # Проверка статуса камеры перед применением настроек
            camera_status = await get_camera_status(camera['ip'])
            if not camera_status:
                logger.error(f"Failed to get status for camera {camera['ip']}, skipping")
                continue
                
            for setting_id, value in current_settings.items():
                if await apply_setting(camera['ip'], setting_id, value):
                    if await verify_setting(camera['ip'], setting_id, value):
                        logger.info(f"Setting {setting_id}={value} successfully applied and verified")
                    else:
                        logger.warning(f"Setting {setting_id}={value} verification failed")
                await asyncio.sleep(0.2)  # Пауза между настройками
                
        # Выводим итоговый отчет
        print_settings_report()

    except Exception as e:
        logger.error(f"Error in main_async: {str(e)}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
        print_settings_report()  # Выводим отчет даже при прерывании
    except Exception as e:
        logger.error(f"Program error: {str(e)}", exc_info=True)
        print_settings_report()  # Выводим отчет даже при ошибке 