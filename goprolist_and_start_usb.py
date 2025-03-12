import requests
import logging
from concurrent.futures import ThreadPoolExecutor
from zeroconf import Zeroconf, ServiceBrowser
from utils import get_app_root, get_data_dir, setup_logging, check_dependencies
import sys
import time
import json

# Инициализируем логирование с именем модуля
logger = setup_logging(__name__)

MAX_DISCOVERY_ATTEMPTS = 3
DISCOVERY_TIMEOUT = 15  # Увеличено с 10 до 15 секунд
USB_CHECK_TIMEOUT = 5

def check_gopro_dependencies():
    """Проверка зависимостей для работы с GoPro"""
    required_files = [
        'data/camera_cache.json',
        'utils.py'
    ]
    
    app_root = get_app_root()
    missing_files = []
    
    for file in required_files:
        if not (app_root / file).exists():
            missing_files.append(file)
    
    if missing_files:
        raise FileNotFoundError(f"Missing required files: {', '.join(missing_files)}")

def check_usb_connection(camera_ip):
    """Проверка USB-соединения с камерой"""
    try:
        url = f"http://{camera_ip}:8080/gopro/camera/state"
        response = requests.get(url, timeout=USB_CHECK_TIMEOUT)
        return response.status_code == 200
    except requests.RequestException:
        return False

class GoProListener:
    def __init__(self):
        self.devices = []
        self.discovered_ips = set()  # Для отслеживания уникальных IP-адресов

    def add_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if info and info.addresses:
            ip_address = ".".join(map(str, info.addresses[0]))
            if ip_address not in self.discovered_ips:  # Проверка на дубликаты
                logging.info(f"Discovered GoPro: {name} at {ip_address}")
                if check_usb_connection(ip_address):  # Проверка USB-соединения
                    self.devices.append({
                        "name": name,
                        "ip": ip_address
                    })
                    self.discovered_ips.add(ip_address)
                else:
                    logging.warning(f"USB connection check failed for camera {name} at {ip_address}")

    def remove_service(self, zeroconf, service_type, name):
        logging.info(f"GoPro {name} removed")
        
    def update_service(self, zeroconf, service_type, name):
        """Обработка обновления сервиса"""
        pass

def discover_gopro_devices():
    """Обнаружение GoPro устройств с повторными попытками"""
    for attempt in range(MAX_DISCOVERY_ATTEMPTS):
        zeroconf = Zeroconf()
        listener = GoProListener()
        logging.info(f"Searching for GoPro cameras (attempt {attempt + 1}/{MAX_DISCOVERY_ATTEMPTS})...")
        browser = ServiceBrowser(zeroconf, "_gopro-web._tcp.local.", listener)

        try:
            time.sleep(DISCOVERY_TIMEOUT)
            if listener.devices:
                logging.info(f"Found {len(listener.devices)} GoPro devices.")
                return listener.devices
        finally:
            zeroconf.close()

        if not listener.devices and attempt < MAX_DISCOVERY_ATTEMPTS - 1:
            logging.warning(f"No devices found on attempt {attempt + 1}, retrying...")
            time.sleep(2)  # Пауза между попытками

    logging.warning("No devices found after all attempts.")
    return []

def save_devices_to_cache(devices, cache_filename="camera_cache.json"):
    """Сохранение списка камер в кэш с проверкой уникальности"""
    try:
        cache_file = get_data_dir() / cache_filename
        
        # Загрузка существующего кэша
        existing_devices = []
        if cache_file.exists():
            try:
                with open(cache_file, "r") as file:
                    existing_devices = json.load(file)
            except json.JSONDecodeError:
                logging.warning("Invalid cache file format, creating new cache")

        # Объединение списков с проверкой уникальности
        unique_devices = {device["ip"]: device for device in existing_devices + devices}
        updated_devices = list(unique_devices.values())

        with open(cache_file, "w") as file:
            json.dump(updated_devices, file, indent=4)
        logging.info(f"Cache updated successfully with {len(updated_devices)} devices.")
    except Exception as e:
        logging.error(f"Failed to save camera cache: {e}")

def reset_and_enable_usb_control(camera_ip):
    """Сброс и включение USB-контроля с повторными попытками"""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            logging.info(f"Resetting USB control on camera {camera_ip} (attempt {attempt + 1}/{max_attempts})")
            toggle_usb_control(camera_ip, enable=False)
            time.sleep(2)
            toggle_usb_control(camera_ip, enable=True)
            if check_usb_connection(camera_ip):
                logging.info(f"USB control successfully reset for camera {camera_ip}")
                return True
        except Exception as e:
            logging.error(f"Error resetting USB control on attempt {attempt + 1}: {e}")
        
        if attempt < max_attempts - 1:
            time.sleep(2)
    
    logging.error(f"Failed to reset USB control for camera {camera_ip} after {max_attempts} attempts")
    return False

def toggle_usb_control(camera_ip, enable):
    """Включение/выключение USB-контроля с таймаутом"""
    action = 1 if enable else 0
    url = f"http://{camera_ip}:8080/gopro/camera/control/wired_usb?p={action}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            logging.info(f"USB control {'enabled' if enable else 'disabled'} on camera {camera_ip}.")
            return True
        else:
            logging.error(f"Failed to {'enable' if enable else 'disable'} USB control on camera {camera_ip}. "
                         f"Status Code: {response.status_code}. Response: {response.text}")
            return False
    except requests.RequestException as e:
        logging.error(f"Error toggling USB control on camera {camera_ip}: {e}")
        return False

def main():
    """Основная функция для подключения к камерам"""
    try:
        # Проверяем зависимости
        check_dependencies()
        check_gopro_dependencies()
        
        devices = discover_gopro_devices()
        if devices:
            logging.info("Found the following GoPro devices:")
            for device in devices:
                logging.info(f"Name: {device['name']}, IP: {device['ip']}")

            save_devices_to_cache(devices)

            with ThreadPoolExecutor() as executor:
                executor.map(lambda d: reset_and_enable_usb_control(d['ip']), devices)
            
            return True
        else:
            logging.error("No GoPro devices found.")
            return False

    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        return False

if __name__ == "__main__":
    main()
