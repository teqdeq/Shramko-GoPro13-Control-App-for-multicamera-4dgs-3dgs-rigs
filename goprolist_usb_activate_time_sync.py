# Copyright (c) 2024 Andrii Shramko
# Contact: zmei116@gmail.com
# LinkedIn: https://www.linkedin.com/in/andrii-shramko/
# Tags: #ShramkoVR #ShramkoCamera #ShramkoSoft
# License: This code is free to use for non-commercial projects.
# For commercial use, please contact Andrii Shramko at the above email or LinkedIn.

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from utils import get_app_root, setup_logging, check_dependencies
from goprolist_and_start_usb import (
    discover_gopro_devices, 
    save_devices_to_cache,
    reset_and_enable_usb_control,
    check_gopro_dependencies
)
import sys

# Initialize logging
setup_logging()

def check_sync_dependencies():
    """Check dependencies for synchronization"""
    required_files = [
        'date_time_sync.py',
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

def sync_time_on_cameras():
    """Synchronize time on the cameras"""
    try:
        from date_time_sync import sync_time
        sync_time()
    except Exception as e:
        logging.error(f"Failed to sync time: {e}")
        raise

if __name__ == "__main__":
    try:
        # Check dependencies
        check_dependencies()
        check_gopro_dependencies()
        check_sync_dependencies()
        
        # Step 1: Discover GoPro devices
        devices = discover_gopro_devices()
        if not devices:
            logging.error("No GoPro devices found.")
            sys.exit(1)

        logging.info("Found the following GoPro devices:")
        for device in devices:
            logging.info(f"Name: {device['name']}, IP: {device['ip']}")

        # Save discovered devices to cache
        save_devices_to_cache(devices)

        # Step 2: Enable USB control on all cameras
        logging.info("Resetting and enabling USB control on all cameras...")
        with ThreadPoolExecutor() as executor:
            executor.map(lambda d: reset_and_enable_usb_control(d['ip']), devices)

        # Step 3: Synchronize time on all cameras
        logging.info("Synchronizing time on all cameras...")
        sync_time_on_cameras()
        time.sleep(1)  # Short pause after synchronization

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        if getattr(sys, 'frozen', False):
            from PyQt5.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error during synchronization")
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Error")
            msg.exec_()
        raise
