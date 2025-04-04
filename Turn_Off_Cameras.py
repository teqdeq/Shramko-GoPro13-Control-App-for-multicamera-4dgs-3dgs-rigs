# Copyright (c) 2024 Andrii Shramko
# Contact: zmei116@gmail.com
# LinkedIn: https://www.linkedin.com/in/andrii-shramko/
# Tags: #ShramkoVR #ShramkoCamera #ShramkoSoft
# License: This code is free to use for non-commercial projects.
# For commercial use, please contact Andrii Shramko at the above email or LinkedIn.

import requests
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from utils import setup_logging, get_data_dir

# Initialize logging
logger = setup_logging(__name__)

def turn_off_camera(camera_ip):
    """Turn off a single camera"""
    try:
        response = requests.get(f"http://{camera_ip}/gp/gpControl/command/system/sleep")
        if response.status_code == 200:
            logger.info(f"Camera {camera_ip} turned off successfully.")
            return True
        else:
            logger.error(f"Failed to turn off camera {camera_ip}. Status Code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"An error occurred while turning off camera {camera_ip}: {e}")
        return False

def main():
    """Main function to turn off all cameras"""
    try:
        # Load devices from cache
        cache_file = get_data_dir() / "camera_cache.json"
        try:
            with open(cache_file, "r") as f:
                devices = json.load(f)
            logger.info("Loaded cached camera devices:")
            for device in devices:
                logger.info(f"Name: {device['name']}, IP: {device['ip']}")
        except FileNotFoundError:
            logger.error("Camera cache not found. Cannot turn off cameras.")
            return False

        # Turn off all cameras
        logger.info("Turning off all cameras...")
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(lambda d: turn_off_camera(d["ip"]), devices))
        
        return all(results)  # Return True only if all cameras were turned off successfully

    except Exception as e:
        logger.error(f"Error in turn off operation: {e}")
        return False

if __name__ == "__main__":
    main()
