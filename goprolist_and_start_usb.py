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

class GoProListener:
    def __init__(self):
        self.devices = []

    def add_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if info:
            ip_address = ".".join(map(str, info.addresses[0]))
            logging.info(f"Discovered GoPro: {name} at {ip_address}")
            self.devices.append({
                "name": name,
                "ip": ip_address
            })

    def remove_service(self, zeroconf, service_type, name):
        logging.info(f"GoPro {name} removed")
        
    def update_service(self, zeroconf, service_type, name):
        """Обработка обновления сервиса"""
        pass  # Пустая реализация, так как нам не нужно обрабатывать обновл��ния

def discover_gopro_devices():
    zeroconf = Zeroconf()
    listener = GoProListener()
    logging.info("Searching for GoPro cameras...")
    browser = ServiceBrowser(zeroconf, "_gopro-web._tcp.local.", listener)

    try:
        time.sleep(5)  # Allow time for discovery
    finally:
        zeroconf.close()

    return listener.devices

def save_devices_to_cache(devices, cache_filename="camera_cache.json"):
    """Сохранение списка камер в кэш"""
    try:
        cache_file = get_data_dir() / cache_filename
        with open(cache_file, "w") as file:
            json.dump(devices, file, indent=4)
        logging.info("Cache updated successfully with newly discovered devices.")
    except Exception as e:
        logging.error(f"Failed to save camera cache: {e}")

def reset_and_enable_usb_control(camera_ip):
    logging.info(f"Resetting USB control on camera {camera_ip}.")
    toggle_usb_control(camera_ip, enable=False)
    time.sleep(2)
    toggle_usb_control(camera_ip, enable=True)

def toggle_usb_control(camera_ip, enable):
    action = 1 if enable else 0
    url = f"http://{camera_ip}:8080/gopro/camera/control/wired_usb?p={action}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            logging.info(f"USB control {'enabled' if enable else 'disabled'} on camera {camera_ip}.")
        else:
            logging.error(f"Failed to {'enable' if enable else 'disable'} USB control on camera {camera_ip}. "
                          f"Status Code: {response.status_code}. Response: {response.text}")
    except requests.RequestException as e:
        logging.error(f"Error toggling USB control on camera {camera_ip}: {e}")

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
