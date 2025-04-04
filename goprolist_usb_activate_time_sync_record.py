# Copyright (c) 2024 Andrii Shramko
# Contact: zmei116@gmail.com
# LinkedIn: https://www.linkedin.com/in/andrii-shramko/
# Tags: #ShramkoVR #ShramkoCamera #ShramkoSoft
# License: This code is free to use for non-commercial projects.
# For commercial use, please contact Andrii Shramko at the above email or LinkedIn.

from zeroconf import Zeroconf, ServiceBrowser
import requests
import time
import logging
import json
from concurrent.futures import ThreadPoolExecutor
from utils import get_app_root, get_data_dir, setup_logging
from date_time_sync import sync_time_on_cameras as sync_time

# Replace the default logging configuration with our custom one from utils
logger = setup_logging(__name__)

class GoProListener:
    def __init__(self):
        self.devices = []

    def add_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if info:
            ip_address = ".".join(map(str, info.addresses[0]))
            logger.info(f"Discovered GoPro: {name} at {ip_address}")
            self.devices.append({
                "name": name.split(".")[0],  # Store only the serial number
                "ip": ip_address
            })

    def remove_service(self, zeroconf, service_type, name):
        logger.info(f"GoPro {name} removed")

# Discover GoPro devices
def discover_gopro_devices():
    zeroconf = Zeroconf()
    listener = GoProListener()
    logger.info("Searching for GoPro cameras...")
    browser = ServiceBrowser(zeroconf, "_gopro-web._tcp.local.", listener)

    try:
        time.sleep(5)  # Allow time for discovery
    finally:
        zeroconf.close()

    return listener.devices

# Enable or reset USB control
def reset_and_enable_usb_control(camera_ip):
    logger.info(f"Resetting USB control on camera {camera_ip}.")
    toggle_usb_control(camera_ip, enable=False)
    time.sleep(2)
    toggle_usb_control(camera_ip, enable=True)

def toggle_usb_control(camera_ip, enable):
    action = 1 if enable else 0
    url = f"http://{camera_ip}:8080/gopro/camera/control/wired_usb?p={action}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            logger.info(f"USB control {'enabled' if enable else 'disabled'} on camera {camera_ip}.")
        else:
            logger.error(f"Failed to {'enable' if enable else 'disable'} USB control on camera {camera_ip}. "
                          f"Status Code: {response.status_code}. Response: {response.text}")
    except requests.RequestException as e:
        logger.error(f"Error toggling USB control on camera {camera_ip}: {e}")

# Start recording
def start_recording(camera_ip):
    try:
        response = requests.get(f"http://{camera_ip}:8080/gopro/camera/shutter/start")
        if response.status_code == 200:
            logger.info(f"Recording started successfully on camera {camera_ip}.")
        else:
            logger.error(f"Failed to start recording on camera {camera_ip}. Status Code: {response.status_code}")
            logger.error(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"An error occurred while starting recording on camera {camera_ip}: {e}")

# Synchronize time on all cameras
def sync_time_on_cameras():
    """Synchronize time on all cameras"""
    try:
        sync_time()
        logger.info("Time synchronization completed successfully")
    except Exception as e:
        logger.error(f"Failed to synchronize time: {e}")
        raise

# Save discovered devices to cache
def save_devices_to_cache(devices, cache_filename="camera_cache.json"):
    try:
        cache_file = get_data_dir() / cache_filename
        with open(cache_file, "w") as file:
            json.dump(devices, file)
        logger.info(f"Successfully saved {len(devices)} devices to cache")
        
        # Create a backup in the root directory
        backup_file = get_app_root() / cache_filename
        with open(backup_file, "w") as file:
            json.dump(devices, file)
        logger.info("Created backup cache file")
    except Exception as e:
        logger.error(f"Failed to save cache: {e}")

# Add a function to load the cache
def load_devices_from_cache(cache_filename="camera_cache.json"):
    cache_file = get_data_dir() / cache_filename
    try:
        if cache_file.exists():
            with open(cache_file, "r") as file:
                return json.load(file)
    except Exception as e:
        logger.error(f"Failed to load camera cache from {cache_file}: {e}")
    return None

def check_dependencies():
    """Check for the presence of all necessary files"""
    required_files = [
        'date_time_sync.py',
        'utils.py',
        'camera_cache.json'
    ]
    
    missing_files = []
    for file in required_files:
        if not (get_app_root() / file).exists():
            missing_files.append(file)
    
    if missing_files:
        raise FileNotFoundError(f"Missing required files: {', '.join(missing_files)}")

def check_record_dependencies():
    """Check dependencies for recording"""
    required_files = [
        'date_time_sync.py',
        'data/camera_cache.json',
        'utils.py',
        'recording.py'
    ]
    
    app_root = get_app_root()
    missing_files = []
    
    for file in required_files:
        if not (app_root / file).exists():
            missing_files.append(file)
    
    if missing_files:
        raise FileNotFoundError(f"Missing required files: {', '.join(missing_files)}")

def main():
    try:
        # Step 1: Discover GoPro devices
        devices = discover_gopro_devices()
        if not devices:
            cached_devices = load_devices_from_cache()
            if cached_devices:
                logger.info("Using cached devices as no live devices found")
                devices = cached_devices
            else:
                logger.error("No GoPro devices found and no cache available.")
                return

        logger.info("Found the following GoPro devices:")
        for device in devices:
            logger.info(f"Name: {device['name']}, IP: {device['ip']}")

        save_devices_to_cache(devices)

        # Step 2: Enable USB control
        logger.info("Enabling USB control on all cameras...")
        with ThreadPoolExecutor() as executor:
            executor.map(lambda d: reset_and_enable_usb_control(d['ip']), devices)

        # Step 3: Synchronize time
        logger.info("Synchronizing time on all cameras...")
        sync_time_on_cameras()
        time.sleep(1)

        # Step 4: Start recording
        logger.info("Starting recording on all cameras...")
        with ThreadPoolExecutor() as executor:
            executor.map(lambda d: start_recording(d['ip']), devices)

    except Exception as e:
        logger.error(f"An error occurred in main execution: {e}")
        raise

if __name__ == "__main__":
    main()
