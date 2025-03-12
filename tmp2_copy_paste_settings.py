import asyncio
import aiohttp
import logging
import time
from goprolist_and_start_usb import discover_gopro_devices
from datetime import datetime
from prime_camera_sn import serial_number as prime_camera_sn

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Загружаем описания настроек
SETTINGS_DESCRIPTIONS = {
    "6": {
        "name": "Video Framing",
        "allowed_values": {
            "0": "16:9",
            "1": "4:3",
            "2": "Full Frame",
            "3": "8:7"
        }
    },
    "13": {
        "name": "Media Format",
        "allowed_values": {
            "13": "Time Lapse Video",
            "20": "Time Lapse Photo",
            "21": "Night Lapse Photo",
            "26": "Night Lapse Video"
        }
    },
    "19": {
        "name": "Photo Mode",
        "allowed_values": {
            "0": "SuperPhoto",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    "24": {
        "name": "Video Bit Rate",
        "allowed_values": {
            "0": "Standard",
            "1": "High",
            "2": "Low"
        }
    },
    "30": {
        "name": "Photo Timelapse Rate",
        "allowed_values": {
            "11": "3 Seconds",
            "100": "60 Minutes",
            "101": "30 Minutes",
            "102": "5 Minutes",
            "103": "2 Minutes",
            "104": "60 Seconds",
            "105": "30 Seconds",
            "106": "10 Seconds",
            "107": "5 Seconds",
            "108": "2 Seconds"
        }
    },
    "31": {
        "name": "Photo Interval Duration",
        "allowed_values": {
            "0": "Off",
            "1": "5 Minutes",
            "2": "10 Minutes",
            "3": "15 Minutes",
            "4": "20 Minutes",
            "5": "30 Minutes",
            "6": "1 Hour",
            "7": "2 Hours",
            "8": "3 Hours",
            "9": "4 Hours",
            "10": "8 Hours"
        }
    },
    "32": {
        "name": "Nightlapse Rate",
        "allowed_values": {
            "1": "Auto",
            "2": "4 Seconds",
            "3": "5 Seconds",
            "4": "10 Seconds",
            "5": "15 Seconds",
            "6": "20 Seconds",
            "7": "30 Seconds",
            "8": "1 Minute",
            "9": "2 Minutes",
            "10": "5 Minutes",
            "11": "30 Minutes",
            "12": "60 Minutes"
        }
    },
    "37": {
        "name": "Photo Single Interval",
        "allowed_values": {
            "0": "Off",
            "1": "0.5s",
            "2": "1s",
            "3": "2s",
            "4": "5s",
            "5": "10s",
            "6": "30s",
            "7": "60s"
        }
    },
    "41": {
        "name": "Video Resolution",
        "allowed_values": {
            "1": "4K",
            "4": "2.7K",
            "9": "1080p",
            "12": "720p",
            "18": "4K 4:3",
            "25": "5K 4:3",
            "26": "5.3K 8:7",
            "100": "5.3K"
        }
    },
    "42": {
        "name": "Frame Rate",
        "allowed_values": {
            "0": "240.0",
            "1": "120.0",
            "2": "100.0",
            "5": "60.0",
            "6": "50.0",
            "8": "30.0",
            "9": "25.0",
            "10": "24.0",
            "13": "200.0"
        }
    },
    "43": {
        "name": "Webcam Digital Lenses",
        "allowed_values": {
            "0": "Wide",
            "2": "Narrow",
            "4": "Linear",
            "7": "Max SuperView"
        }
    },
    "47": {
        "name": "Video Lens",
        "allowed_values": {
            "0": "Wide",
            "2": "Narrow",
            "3": "Superview",
            "4": "Linear",
            "7": "Max SuperView",
            "8": "Linear + Horizon Leveling",
            "9": "HyperView",
            "10": "Linear + Horizon Lock"
        }
    },
    "54": {
        "name": "Anti-Flicker",
        "allowed_values": {
            "0": "NTSC",
            "1": "PAL",
            "2": "60Hz",
            "3": "50Hz"
        }
    },
    "59": {
        "name": "Auto Power Down",
        "allowed_values": {
            "0": "Never",
            "1": "1 Min",
            "4": "5 Min",
            "6": "15 Min",
            "7": "30 Min"
        }
    },
    "60": {
        "name": "Controls",
        "allowed_values": {
            "0": "Easy",
            "1": "Pro"
        }
    },
    "61": {
        "name": "Easy Mode Speed",
        "allowed_values": {
            "0": "8X Ultra Slo-Mo",
            "1": "4X Slo-Mo",
            "2": "2X Slo-Mo",
            "3": "Real Speed",
            "4": "2X Speed Up",
            "5": "4X Speed Up",
            "6": "8X Speed Up",
            "7": "15X Speed Up",
            "8": "30X Speed Up"
        }
    },
    "62": {
        "name": "Easy Night Photo",
        "allowed_values": {
            "0": "Super Photo",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    "66": {
        "name": "Enable Night Photo",
        "allowed_values": {
            "0": "Off",
            "1": "On"
        }
    },
    "75": {
        "name": "Photo Output",
        "allowed_values": {
            "0": "Standard",
            "1": "Raw",
            "2": "HDR",
            "3": "SuperPhoto"
        }
    },
    "87": {
        "name": "Profiles",
        "allowed_values": {
            "0": "Standard",
            "1": "Vibrant",
            "2": "Natural",
            "3": "Flat",
            "100": "Standard (Extended)"
        }
    },
    "88": {
        "name": "Setup Screen Saver",
        "allowed_values": {
            "0": "Never",
            "1": "1 Min",
            "2": "2 Min",
            "3": "3 Min",
            "4": "5 Min"
        }
    },
    "91": {
        "name": "Video Framing",
        "allowed_values": {
            "0": "16:9",
            "1": "4:3",
            "2": "Full Frame",
            "3": "8:7"
        }
    },
    "102": {
        "name": "Frame Rate",
        "allowed_values": {
            "0": "240.0",
            "1": "120.0",
            "2": "100.0",
            "5": "60.0",
            "6": "50.0",
            "8": "30.0",
            "9": "25.0",
            "10": "24.0",
            "13": "200.0"
        }
    },
    "105": {
        "name": "Photo Lens",
        "allowed_values": {
            "19": "Narrow",
            "100": "Max SuperView",
            "101": "Wide",
            "102": "Linear"
        }
    },
    "111": {
        "name": "Video Aspect Ratio",
        "allowed_values": {
            "0": "4:3",
            "1": "16:9",
            "2": "Full Frame",
            "3": "8:7"
        }
    },
    "112": {
        "name": "Setup Language",
        "allowed_values": {
            "0": "English",
            "1": "Chinese",
            "2": "Japanese",
            "3": "Korean",
            "4": "Spanish",
            "5": "French",
            "6": "German",
            "7": "Italian",
            "8": "Portuguese",
            "9": "Russian",
            "255": "System Default"
        }
    },
    "114": {
        "name": "Framing",
        "allowed_values": {
            "0": "Horizontal",
            "1": "Vertical"
        }
    },
    "115": {
        "name": "Lapse Mode",
        "allowed_values": {
            "0": "TimeWarp",
            "1": "Time Lapse",
            "2": "Night Lapse"
        }
    },
    "116": {
        "name": "Multi Shot Aspect Ratio",
        "allowed_values": {
            "0": "16:9",
            "1": "4:3",
            "2": "Full Frame",
            "3": "8:7"
        }
    },
    "117": {
        "name": "Multi Shot Framing",
        "allowed_values": {
            "0": "16:9",
            "1": "4:3",
            "2": "Full Frame",
            "3": "8:7"
        }
    },
    "118": {
        "name": "Star Trails Length",
        "allowed_values": {
            "0": "15 Minutes",
            "1": "30 Minutes",
            "2": "1 Hour",
            "3": "2 Hours",
            "4": "4 Hours"
        }
    },
    "121": {
        "name": "Video Lens",
        "allowed_values": {
            "0": "Wide",
            "2": "Narrow",
            "3": "Superview",
            "4": "Linear",
            "7": "Max SuperView",
            "8": "Linear + Horizon Leveling",
            "9": "HyperView",
            "10": "Linear + Horizon Lock",
            "11": "Max HyperView",
            "12": "Ultra SuperView",
            "13": "Ultra Wide",
            "104": "Ultra HyperView"
        }
    },
    "122": {
        "name": "Photo Lens",
        "allowed_values": {
            "0": "Wide 12 MP",
            "10": "Linear 12 MP",
            "19": "Narrow",
            "27": "Wide 23 MP",
            "28": "Linear 13 MP",
            "31": "Wide 27 MP",
            "32": "Linear 27 MP",
            "41": "Ultra Wide 12 MP",
            "100": "Max SuperView",
            "101": "Wide",
            "102": "Linear"
        }
    },
    "123": {
        "name": "Time Lapse Digital Lenses",
        "allowed_values": {
            "19": "Narrow",
            "31": "Wide 27 MP",
            "32": "Linear 27 MP",
            "100": "Max SuperView",
            "101": "Wide",
            "102": "Linear"
        }
    },
    "124": {
        "name": "Photo Output",
        "allowed_values": {
            "0": "Standard",
            "1": "Raw",
            "2": "HDR",
            "100": "SuperPhoto"
        }
    },
    "126": {
        "name": "System Video Mode",
        "allowed_values": {
            "0": "Highest Quality",
            "1": "Extended Battery",
            "2": "Standard Quality"
        }
    },
    "129": {
        "name": "Video Framing",
        "allowed_values": {
            "0": "16:9",
            "1": "4:3",
            "2": "Full Frame",
            "3": "8:7"
        }
    },
    "130": {
        "name": "Video Resolution",
        "allowed_values": {
            "1": "4K",
            "4": "2.7K",
            "9": "1080p",
            "12": "720p",
            "18": "4K 4:3",
            "25": "5K 4:3",
            "26": "5.3K 8:7",
            "27": "5.3K 4:3",
            "28": "4K 8:7",
            "37": "4K 1:1",
            "38": "900",
            "100": "5.3K",
            "105": "5.3K",
            "107": "5.3K 8:7 V2",
            "108": "4K 8:7 V2",
            "109": "4K 9:16 V2",
            "110": "1080 9:16 V2",
            "111": "2.7K 4:3 V2"
        }
    },
    "135": {
        "name": "Hypersmooth",
        "allowed_values": {
            "0": "Off",
            "1": "Low",
            "2": "High",
            "3": "Boost",
            "4": "Auto Boost",
            "100": "Standard"
        }
    },
    "139": {
        "name": "Hypersmooth",
        "allowed_values": {
            "0": "Off",
            "1": "On",
            "2": "High",
            "3": "Boost",
            "4": "Auto Boost"
        }
    },
    "145": {
        "name": "Photo Mode",
        "allowed_values": {
            "0": "SuperPhoto",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    "147": {
        "name": "Enable Night Photo",
        "allowed_values": {
            "0": "Off",
            "1": "On"
        }
    },
    "148": {
        "name": "Video Bit Rate",
        "allowed_values": {
            "0": "Standard",
            "1": "High",
            "100": "High"
        }
    },
    "158": {
        "name": "Controls",
        "allowed_values": {
            "0": "Easy",
            "1": "Pro"
        }
    },
    "159": {
        "name": "Easy Night Photo",
        "allowed_values": {
            "0": "Super Photo",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    "160": {
        "name": "Enable Night Photo",
        "allowed_values": {
            "0": "Off",
            "1": "On"
        }
    },
    "161": {
        "name": "Photo Output",
        "allowed_values": {
            "0": "Standard",
            "1": "Raw",
            "2": "HDR",
            "100": "SuperPhoto"
        }
    },
    "162": {
        "name": "Max Lens",
        "allowed_values": {
            "0": "Off",
            "1": "On"
        }
    },
    "167": {
        "name": "HindSight",
        "allowed_values": {
            "2": "15 Seconds",
            "3": "30 Seconds",
            "4": "Off"
        }
    },
    "168": {
        "name": "Wireless Band",
        "allowed_values": {
            "0": "2.4GHz",
            "1": "5GHz",
            "2": "Auto"
        }
    },
    "173": {
        "name": "Video Performance Mode",
        "allowed_values": {
            "0": "Maximum Video Performance",
            "1": "Extended Battery",
            "2": "Tripod / Stationary Video"
        }
    },
    "44": {
        "name": "Video Resolution",
        "allowed_values": {
            "1": "4K",
            "4": "2.7K",
            "9": "1080p",
            "12": "720p",
            "18": "4K 4:3",
            "25": "5K 4:3",
            "26": "5.3K 8:7",
            "100": "5.3K"
        }
    },
    "45": {
        "name": "Video Timelapse Rate",
        "allowed_values": {
            "0": "0.5 Seconds",
            "1": "1 Second",
            "2": "2 Seconds",
            "3": "5 Seconds",
            "4": "10 Seconds",
            "5": "30 Seconds",
            "6": "60 Seconds",
            "7": "2 Minutes",
            "8": "5 Minutes",
            "9": "30 Minutes",
            "10": "60 Minutes"
        }
    },
    "48": {
        "name": "Video Lens",
        "allowed_values": {
            "0": "Wide",
            "2": "Narrow",
            "3": "Superview",
            "4": "Linear",
            "7": "Max SuperView",
            "8": "Linear + Horizon Leveling",
            "9": "HyperView",
            "10": "Linear + Horizon Lock"
        }
    },
    "76": {
        "name": "Photo Mode",
        "allowed_values": {
            "0": "SuperPhoto",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    "128": {
        "name": "Media Format",
        "allowed_values": {
            "12": "Time Lapse Video (Legacy)",
            "13": "Time Lapse Video",
            "20": "Time Lapse Photo",
            "21": "Night Lapse Photo",
            "26": "Night Lapse Video"
        }
    },
    "144": {
        "name": "Video Resolution",
        "allowed_values": {
            "1": "4K",
            "4": "2.7K",
            "9": "1080p",
            "12": "720p",
            "18": "4K 4:3",
            "25": "5K 4:3",
            "26": "5.3K 8:7",
            "27": "5.3K 4:3",
            "28": "4K 8:7",
            "37": "4K 1:1",
            "38": "900",
            "100": "5.3K",
            "107": "5.3K 8:7 V2",
            "108": "4K 8:7 V2",
            "109": "4K 9:16 V2",
            "110": "1080 9:16 V2",
            "111": "2.7K 4:3 V2"
        }
    },
    "146": {
        "name": "Photo Output",
        "allowed_values": {
            "0": "Standard",
            "1": "Raw",
            "2": "HDR",
            "100": "SuperPhoto"
        }
    },
    "155": {
        "name": "Photo Mode",
        "allowed_values": {
            "0": "SuperPhoto",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    "165": {
        "name": "Photo Mode",
        "allowed_values": {
            "0": "SuperPhoto",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    "166": {
        "name": "Easy Night Photo",
        "allowed_values": {
            "0": "Super Photo",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    "169": {
        "name": "Controls",
        "allowed_values": {
            "0": "Easy",
            "1": "Pro"
        }
    }
}

# Настройки для тестирования
TEST_DELAYS = [0, 0.1, 1.0]  # Задержки в секундах для тестирования
TEST_RESULTS = {delay: {'success': 0, 'failed': 0, 'failed_settings': []} for delay in TEST_DELAYS}

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
            url = f"http://{camera_ip}:8080/gp/gpControl/status"
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    state = await response.json()
                    current_value = state.get('settings', {}).get(str(setting_id))
                    if str(current_value) == str(expected_value):
                        return True
                await asyncio.sleep(0.1)  # Минимальная пауза для проверки
        except Exception as e:
            logging.error(f"Error verifying setting {setting_id}: {e}")
    return False

async def apply_single_setting(session, camera_ip, setting_id, value, delay):
    """Применение одной настройки к камере"""
    try:
        url = f"http://{camera_ip}:8080/gp/gpControl/setting/{setting_id}/{value}"
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                # Проверяем успешность применения
                if await verify_setting_applied(session, camera_ip, setting_id, value):
                    TEST_RESULTS[delay]['success'] += 1
                    logging.info(f"Successfully applied setting {setting_id}={value} to camera {camera_ip}")
                    return True
                else:
                    TEST_RESULTS[delay]['failed'] += 1
                    TEST_RESULTS[delay]['failed_settings'].append((setting_id, value))
                    logging.warning(f"Failed to verify setting {setting_id}={value} on camera {camera_ip}")
            else:
                TEST_RESULTS[delay]['failed'] += 1
                TEST_RESULTS[delay]['failed_settings'].append((setting_id, value))
                logging.error(f"Failed to apply setting {setting_id}={value} to camera {camera_ip}")
            return False
    except Exception as e:
        TEST_RESULTS[delay]['failed'] += 1
        TEST_RESULTS[delay]['failed_settings'].append((setting_id, value))
        logging.error(f"Error applying setting {setting_id}: {e}")
        return False

async def apply_settings_batch(session, camera_ip, settings_batch, delay):
    """Применение группы настроек к камере"""
    results = []
    for setting_id, value in settings_batch:
        success = await apply_single_setting(session, camera_ip, setting_id, value, delay)
        results.append((setting_id, success))
        if delay > 0:
            await asyncio.sleep(delay)  # Пауза между настройками
    return results

def get_setting_description(setting_id, value):
    """Получает описание настройки из файла describe_all_camera_settings.py"""
    setting_str = str(setting_id)
    if setting_str in SETTINGS_DESCRIPTIONS:
        setting_info = SETTINGS_DESCRIPTIONS[setting_str]
        value_str = str(value)
        allowed_values = setting_info.get('allowed_values', {})
        value_meaning = allowed_values.get(value_str, "Unknown value")
        return f"{setting_info['name']} ({value_meaning})"
    return f"Unknown setting {setting_id}"

async def test_settings_with_delay(prime_camera, other_cameras, settings_to_apply, delay):
    """Тестирование применения настроек с заданной задержкой"""
    logging.info(f"\nTesting with {delay} seconds delay between settings")
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for camera in other_cameras:
            task = apply_settings_batch(session, camera['ip'], settings_to_apply, delay)
            tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks)
        
        success = TEST_RESULTS[delay]['success']
        failed = TEST_RESULTS[delay]['failed']
        total = success + failed
        success_rate = (success / total * 100) if total > 0 else 0
        
        logging.info(f"\nРезультаты для задержки {delay}с:")
        logging.info(f"Всего настроек: {total}")
        logging.info(f"Успешно применено: {success}")
        logging.info(f"Не удалось применить: {failed}")
        logging.info(f"Процент успеха: {success_rate:.2f}%")
        
        if TEST_RESULTS[delay]['failed_settings']:
            logging.info("\nНе удалось применить следующие настройки:")
            for setting_id, value in TEST_RESULTS[delay]['failed_settings']:
                desc = get_setting_description(setting_id, value)
                logging.info(f"- {desc} (ID: {setting_id}, Value: {value})")

async def main_async(devices):
    """Основная асинхронная функция"""
    try:
        if not devices:
            logging.error("[ASYNC] No cameras found")
            return
            
        # Находим prime камеру
        async with aiohttp.ClientSession() as session:
            prime_camera = None
            other_cameras = []
            
            for device in devices:
                if await is_prime_camera_async(session, device['ip']):
                    prime_camera = device
                else:
                    other_cameras.append(device)
            
            if not prime_camera:
                logging.error("Prime camera not found")
                return
                
            logging.info(f"Prime camera: {prime_camera['ip']}")
            logging.info(f"Other cameras: {[c['ip'] for c in other_cameras]}")
            
            # Получаем настройки с prime камеры
            url = f"http://{prime_camera['ip']}:8080/gp/gpControl/status"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    settings = data.get('settings', {})
                    settings_to_apply = [(int(k), int(v)) for k, v in settings.items()]
                    
                    logging.info(f"\nНайдено настроек на prime камере: {len(settings_to_apply)}")
                    
                    # Тестируем каждую задержку
                    for delay in TEST_DELAYS:
                        await test_settings_with_delay(prime_camera, other_cameras, settings_to_apply, delay)
                        
                    # Выводим итоговое сравнение
                    logging.info("\nИтоговое сравнение:")
                    for delay in TEST_DELAYS:
                        success = TEST_RESULTS[delay]['success']
                        failed = TEST_RESULTS[delay]['failed']
                        total = success + failed
                        success_rate = (success / total * 100) if total > 0 else 0
                        logging.info(f"Задержка {delay}с - Успешно: {success_rate:.2f}% ({success}/{total})")
                        
    except Exception as e:
        logging.error(f"[ASYNC] Error in main: {e}")

def main():
    """Точка входа"""
    try:
        logging.info("[ASYNC] Starting settings application test")
        
        # Ищем камеры
        logging.info("Discovering cameras...")
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