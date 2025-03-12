import asyncio
import aiohttp
import logging
import time
from goprolist_and_start_usb import discover_gopro_devices
from datetime import datetime

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Настройки System Video Mode (ID 126)
SYSTEM_VIDEO_MODE = {
    'id': 126,
    'name': 'System Video Mode',
    'values': {
        0: 'Highest Quality',
        1: 'Extended Battery',
        2: 'Standard Quality'
    },
    'supported_cameras': [
        'HERO13 Black',
        'HERO12 Black',
        'HERO11 Black',
        'HERO10 Black',
        'HERO9 Black'
    ]
}

def get_current_time():
    """Получение текущего времени с миллисекундами"""
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
                    mode_name = SYSTEM_VIDEO_MODE['values'].get(value, 'Unknown')
                    logging.info(f"Successfully set {mode_name} mode ({value}) to camera {camera_ip}")
                    return True
                else:
                    logging.warning(f"Failed to verify setting {setting_id}={value} on camera {camera_ip}")
            else:
                logging.error(f"Failed to apply setting {setting_id}={value} to camera {camera_ip}")
            return False
    except Exception as e:
        logging.error(f"Error applying setting {setting_id}: {e}")
        return False

async def apply_system_video_mode_to_cameras(cameras, mode):
    """Параллельное применение System Video Mode ко всем камерам"""
    if mode not in SYSTEM_VIDEO_MODE['values']:
        logging.error(f"Invalid mode value: {mode}")
        return

    async with aiohttp.ClientSession() as session:
        tasks = []
        for camera in cameras:
            # Создаем задачу для применения настройки
            task = apply_single_setting(session, camera['ip'], SYSTEM_VIDEO_MODE['id'], mode)
            tasks.append(task)

        if tasks:
            # Ждем завершения всех задач
            results = await asyncio.gather(*tasks)
            
            # Анализируем результаты
            for camera_idx, success in enumerate(results):
                if not success:
                    logging.warning(f"Failed to apply System Video Mode to camera {cameras[camera_idx]['ip']}")
        else:
            logging.warning("No tasks created for cameras")

async def cycle_video_modes(devices):
    """Циклическое изменение режимов видео"""
    try:
        # Проверяем камеры перед началом цикла
        async with aiohttp.ClientSession() as session:
            for device in devices:
                model, firmware = await get_camera_info_async(session, device['ip'])
                if not model or model not in SYSTEM_VIDEO_MODE['supported_cameras']:
                    logging.warning(f"Camera {device['ip']} ({model}) is not supported")
                    return

        # Начинаем бесконечный цикл изменения режимов
        mode_values = list(SYSTEM_VIDEO_MODE['values'].items())
        current_idx = 0
        
        while True:
            mode, mode_name = mode_values[current_idx]
            logging.info(f"\nChanging to {mode_name} mode ({mode})")
            
            # Применяем текущий режим
            await apply_system_video_mode_to_cameras(devices, mode)
            
            # Переходим к следующему режиму
            current_idx = (current_idx + 1) % len(mode_values)
            
            # Ждем 4 секунды перед следующим изменением
            await asyncio.sleep(4)
            
    except asyncio.CancelledError:
        logging.info("Cycle stopped by user")
    except Exception as e:
        logging.error(f"Error in cycle_video_modes: {e}")

async def main_async(devices):
    """Основная асинхронная функция"""
    try:
        if not devices:
            logging.error("[ASYNC] No cameras found")
            return
            
        # Проверяем структуру устройств
        for device in devices:
            logging.info(f"Device: {device}")
            
        # Запускаем циклическое изменение режимов
        await cycle_video_modes(devices)
        
    except Exception as e:
        logging.error(f"[ASYNC] Error in main: {e}")

def main():
    """Точка входа"""
    try:
        logging.info(f"[ASYNC] Starting program at {get_current_time()}")
        
        # Ищем камеры только один раз
        logging.info("Discovering cameras...")
        devices = discover_gopro_devices()
        logging.info(f"Found devices: {devices}")
        
        if not devices:
            logging.error("No cameras found")
            return
            
        # Запускаем циклическое изменение режимов
        asyncio.run(main_async(devices))
        
    except KeyboardInterrupt:
        logging.info("Program stopped by user")
    except Exception as e:
        logging.error(f"Error in main: {e}", exc_info=True)

if __name__ == "__main__":
    main() 