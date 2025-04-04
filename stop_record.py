# Copyright (c) 2024 Andrii Shramko
# Contact: zmei116@gmail.com
# LinkedIn: https://www.linkedin.com/in/andrii-shramko/
# Tags: #ShramkoVR #ShramkoCamera #ShramkoSoft
# License: This code is free to use for non-commercial projects.
# For commercial use, please contact Andrii Shramko at the above email or LinkedIn.

import requests
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Thread
from utils import get_app_root, get_data_dir, setup_logging, check_dependencies
import sys

# Initialize logging
setup_logging()

def check_stop_record_dependencies():
    """Check specific dependencies for stop_record"""
    required_files = [
        'data/camera_cache.json',
        'utils.py'
    ]
    
    missing_files = []
    app_root = get_app_root()
    
    for file in required_files:
        if not (app_root / file).exists():
            missing_files.append(file)
    
    if missing_files:
        raise FileNotFoundError(f"Missing required files: {', '.join(missing_files)}")

def check_camera_connection(camera_ip, timeout=2):
    """Check camera availability before stopping recording"""
    try:
        response = requests.get(f"http://{camera_ip}:8080/gopro/camera/state", timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False

def stop_recording_synchronized(devices):
    """Synchronized stop recording on all cameras"""
    # First, check camera availability
    available_devices = []
    unavailable_devices = []
    
    for device in devices:
        if check_camera_connection(device['ip']):
            available_devices.append(device)
        else:
            logging.error(f"Camera {device['ip']} is not accessible")
            unavailable_devices.append(device['ip'])
    
    if not available_devices:
        logging.error("No cameras are accessible")
        return False
        
    # Create a barrier only for available cameras
    barrier = None
    try:
        barrier = Barrier(len(available_devices), timeout=10)  # Increase barrier timeout to 10 seconds
    except Exception as e:
        logging.error(f"Failed to create barrier: {e}")
        return False

    results = []

    def stop_camera(camera_ip):
        try:
            logging.info(f"Camera {camera_ip} waiting for synchronized stop")
            try:
                barrier.wait()
            except Exception as e:
                logging.error(f"Barrier wait failed for camera {camera_ip}: {e}")
                return False

            for attempt in range(3):  # Add 3 attempts to stop
                try:
                    response = requests.get(
                        f"http://{camera_ip}:8080/gopro/camera/shutter/stop",
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        logging.info(f"Camera {camera_ip} stopped successfully")
                        return True
                    elif response.status_code == 503:
                        logging.warning(f"Camera {camera_ip} returned 503, attempt {attempt + 1}/3")
                        time.sleep(1)  # Wait one second before retrying
                    else:
                        logging.error(f"Failed to stop camera {camera_ip}. Status: {response.status_code}")
                        return False
                except requests.RequestException as e:
                    if attempt < 2:  # If this is not the last attempt
                        logging.warning(f"Request failed for camera {camera_ip}, attempt {attempt + 1}/3: {e}")
                        time.sleep(1)
                    else:
                        logging.error(f"Failed to stop camera {camera_ip} after 3 attempts: {e}")
                        return False
            
            return False  # If all attempts failed
        except Exception as e:
            logging.error(f"Error stopping camera {camera_ip}: {e}")
            return False

    # Start threads only for available cameras
    threads = []
    for device in available_devices:
        thread = Thread(target=lambda d=device: results.append((d['ip'], stop_camera(d['ip']))))
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish with a timeout
    for thread in threads:
        thread.join(timeout=15)  # Increase timeout to 15 seconds

    # Check results
    success = True
    failed_cameras = []
    
    for ip, result in results:
        if not result:
            success = False
            failed_cameras.append(ip)
    
    if success:
        logging.info("All accessible cameras stopped successfully")
    else:
        logging.error(f"Failed to stop cameras: {failed_cameras}")
        
    if unavailable_devices:
        logging.warning(f"The following cameras were not accessible: {unavailable_devices}")

    return success

def load_devices_from_cache(cache_filename="camera_cache.json"):
    """Load the list of cameras from cache with portability support"""
    cache_paths = [
        get_data_dir() / cache_filename,  # Primary path
        get_app_root() / 'data' / cache_filename,  # Alternative path
        get_app_root() / cache_filename  # Backup path
    ]
    
    for cache_file in cache_paths:
        try:
            if cache_file.exists():
                with open(cache_file, "r") as file:
                    devices = json.load(file)
                    logging.info(f"Loaded camera cache from {cache_file}")
                    return devices
        except Exception as e:
            logging.warning(f"Failed to load camera cache from {cache_file}: {e}")
            continue
    
    logging.error("No valid camera cache found")
    return None

def main():
    try:
        # Check dependencies before starting
        check_dependencies()
        check_stop_record_dependencies()
        
        devices = load_devices_from_cache()
        if not devices:
            logging.error("Camera cache not found or empty. Cannot stop recording.")
            return False

        logging.info("Loaded cached camera devices:")
        for device in devices:
            logging.info(f"Name: {device['name']}, IP: {device['ip']}")

        logging.info("Stopping recording on all cameras...")
        return stop_recording_synchronized(devices)

    except Exception as e:
        logging.error(f"An error occurred in main execution: {e}")
        if getattr(sys, 'frozen', False):
            from PyQt5.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error stopping recording")
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Error")
            msg.exec_()
        raise

if __name__ == "__main__":
    main()
