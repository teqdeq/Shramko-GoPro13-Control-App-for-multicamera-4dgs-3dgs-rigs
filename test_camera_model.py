import requests
import logging
from goprolist_and_start_usb import discover_gopro_devices, main as connect_usb
import time

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_camera_info(camera_ip):
    """Получение информации о камере через официальные API эндпоинты"""
    try:
        # Получаем информацию о камере
        info_url = f"http://{camera_ip}:8080/gp/gpControl/info"
        info_response = requests.get(info_url, timeout=5)
        info_response.raise_for_status()
        info = info_response.json()
        
        # Получаем состояние камеры
        state_url = f"http://{camera_ip}:8080/gp/gpControl/status"
        state_response = requests.get(state_url, timeout=5)
        state_response.raise_for_status()
        state = state_response.json()
        
        model_name = info.get("info", {}).get("model_name")
        firmware = info.get("info", {}).get("firmware_version")
        
        logging.info(f"\nCamera Info for {camera_ip}:")
        logging.info(f"Model Name: {model_name}")
        logging.info(f"Firmware: {firmware}")
        logging.info(f"State: {state}")
        
        return model_name, state
        
    except Exception as e:
        logging.error(f"Error getting camera info: {e}")
        return None, None

def main():
    try:
        # Подключаем камеры по USB
        logging.info("Connecting cameras via USB...")
        connect_usb()
        
        # Ищем камеры
        logging.info("\nDiscovering cameras...")
        devices = discover_gopro_devices()
        
        if not devices:
            logging.error("No cameras found")
            return
            
        # Получаем информацию о каждой камере
        for device in devices:
            logging.info(f"\nChecking camera: {device['name']}")
            model, state = get_camera_info(device['ip'])
            if model and state:
                logging.info(f"Confirmed camera: {model} (State: {state})")
            else:
                logging.error(f"Failed to get info for camera {device['ip']}")
            
    except Exception as e:
        logging.error(f"Error in main: {e}")

if __name__ == "__main__":
    main() 