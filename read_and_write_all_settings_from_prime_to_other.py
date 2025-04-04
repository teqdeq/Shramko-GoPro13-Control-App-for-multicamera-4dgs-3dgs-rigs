# Copyright (c) 2024 Andrii Shramko
# Contact: zmei116@gmail.com
# LinkedIn: https://www.linkedin.com/in/andrii-shramko/
# Tags: #ShramkoVR #ShramkoCamera #ShramkoSoft
# License: This code is free to use for non-commercial projects.
# For commercial use, please contact Andrii Shramko at the above email or LinkedIn.

import requests
import logging
from goprolist_and_start_usb import discover_gopro_devices
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor
from utils import get_app_root, setup_logging, check_dependencies
import sys
import time
from PyQt5.QtWidgets import QApplication
from progress_dialog import SettingsProgressDialog

# Initialize logging
setup_logging()

# Dictionary of supported settings for each model
CAMERA_SETTINGS = {
    'HERO13': {
        'anti_flicker': {'id': 134, 'values': [0, 1]},  # 0=60Hz, 1=50Hz
        'auto_power_down': {'id': 59, 'values': [0, 1, 2, 3, 4]},  # 0=Never, 1=1min, 2=5min, 3=15min, 4=30min
        'beep_volume': {'id': 87, 'values': [0, 40, 70, 100]},  # 0=Mute, 40=Low, 70=Medium, 100=High
        'video_format': {'id': 79, 'values': [9, 10, 11, 12]},  # 9=HEVC, 10=H264+HEVC, 11=H264, 12=Max Compatibility
        'video_resolution': {'id': 2, 'values': [1, 4, 9, 12, 18, 27, 37, 38]},  # Various resolutions
        'fps': {'id': 3, 'values': [1, 2, 5, 6, 8, 9, 10, 13]},  # Various FPS values
        'lens': {'id': 121, 'values': [0, 4, 7, 9]},  # Various lens modes
        'hypersmooth': {'id': 135, 'values': [0, 1, 2, 3]},  # 0=Off, 1=On, 2=High, 3=Boost
        'bit_depth': {'id': 183, 'values': [0, 2]},  # 0=8bit, 2=10bit
        'white_balance': {'id': 11, 'values': [0, 1, 2, 3, 4, 8]},  # Auto, 3000K, 4000K, 5500K, 6500K, Native
        'iso_max': {'id': 13, 'values': [0, 1, 2, 3, 4, 5]},  # 100, 200, 400, 800, 1600, 3200
        'iso_min': {'id': 102, 'values': [0, 1, 2, 3, 4]},  # 100, 200, 400, 800, 1600
        'sharpness': {'id': 14, 'values': [0, 1, 2]},  # Low, Medium, High
        'ev_comp': {'id': 15, 'values': [0, 1, 2, 3, 4, 5, 6, 7, 8]},  # -2.0 to +2.0
        'photo_resolution': {'id': 17, 'values': [12, 18, 27]},  # Various photo resolutions
        'raw_photo': {'id': 82, 'values': [0, 1]},  # 0=Off, 1=On
        'media_format': {'id': 128, 'values': [1]},  # 1=Format SD Card
        'camera_orientation': {'id': 52, 'values': [0, 1]},  # 0=Up, 1=Down
        'quick_capture': {'id': 54, 'values': [0, 1]},  # 0=Off, 1=On
        'led_status': {'id': 55, 'values': [0, 1, 2, 3, 4]},  # Off, Front Only, All On, Back Only, Front+Top
        'video_compression': {'id': 60, 'values': [0, 1]},  # 0=Standard (H.264), 1=High Efficiency (HEVC)
        'gps_status': {'id': 83, 'values': [0, 1]},  # 0=Off, 1=On
        'voice_control': {'id': 86, 'values': [0, 1]},  # 0=Off, 1=On
        'wake_on_voice': {'id': 104, 'values': [0, 1]},  # 0=Off, 1=On
        'wifi_band': {'id': 105, 'values': [0, 1]},  # 0=2.4GHz, 1=5GHz
        'star_trail': {'id': 106, 'values': [0, 1]},  # 0=Off, 1=On
        'media_mod': {'id': 107, 'values': [0, 1, 2]},  # 0=None, 1=Media Mod, 2=Max Lens Mod
        'webcam_fov': {'id': 108, 'values': [0, 1, 2]},  # 0=Wide, 1=Linear, 2=Narrow
        'webcam_output': {'id': 109, 'values': [0, 1]},  # 0=1080p, 1=720p
        'max_lens_mod': {'id': 110, 'values': [0, 1]},  # 0=Off, 1=On
        'lens_mode': {'id': 111, 'values': [0, 1]},  # 0=Single, 1=Dual
        'hindsight': {'id': 112, 'values': [0, 1, 2]},  # 0=Off, 1=15s, 2=30s
        'scheduled_capture': {'id': 113, 'values': [0, 1]},  # 0=Off, 1=On
        'duration_capture': {'id': 114, 'values': [0, 1]},  # 0=Off, 1=On
    },
    'HERO12': {
        'anti_flicker': {'id': 134, 'values': [0, 1]},  # 0=60Hz, 1=50Hz
        'auto_power_down': {'id': 59, 'values': [0, 1, 2, 3, 4]},  # 0=Never, 1=1min, 2=5min, 3=15min, 4=30min
        'beep_volume': {'id': 87, 'values': [0, 40, 70, 100]},  # 0=Mute, 40=Low, 70=Medium, 100=High
        'video_format': {'id': 79, 'values': [9, 10, 11]},  # 9=HEVC, 10=H264+HEVC, 11=H264
        'video_resolution': {'id': 2, 'values': [1, 4, 9, 12, 18, 27]},  # Various resolutions
        'fps': {'id': 3, 'values': [1, 2, 5, 6, 8, 9, 10]},  # Various FPS values
        'lens': {'id': 121, 'values': [0, 4, 7]},  # Various lens modes
        'hypersmooth': {'id': 135, 'values': [0, 1, 2, 3]},  # 0=Off, 1=On, 2=High, 3=Boost
        'bit_depth': {'id': 183, 'values': [0, 2]},  # 0=8bit, 2=10bit
        'white_balance': {'id': 11, 'values': [0, 1, 2, 3, 4, 8]},  # Auto, 3000K, 4000K, 5500K, 6500K, Native
        'iso_max': {'id': 13, 'values': [0, 1, 2, 3, 4, 5]},  # 100, 200, 400, 800, 1600, 3200
        'iso_min': {'id': 102, 'values': [0, 1, 2, 3, 4]},  # 100, 200, 400, 800, 1600
        'sharpness': {'id': 14, 'values': [0, 1, 2]},  # Low, Medium, High
        'ev_comp': {'id': 15, 'values': [0, 1, 2, 3, 4, 5, 6, 7, 8]},  # -2.0 to +2.0
        'photo_resolution': {'id': 17, 'values': [12, 18, 27]},  # Various photo resolutions
        'raw_photo': {'id': 82, 'values': [0, 1]},  # 0=Off, 1=On
        'media_format': {'id': 128, 'values': [1]},  # 1=Format SD Card
        'camera_orientation': {'id': 52, 'values': [0, 1]},  # 0=Up, 1=Down
        'quick_capture': {'id': 54, 'values': [0, 1]},  # 0=Off, 1=On
        'led_status': {'id': 55, 'values': [0, 1, 2, 3, 4]},  # Off, Front Only, All On, Back Only, Front+Top
        'video_compression': {'id': 60, 'values': [0, 1]},  # 0=Standard (H.264), 1=High Efficiency (HEVC)
        'gps_status': {'id': 83, 'values': [0, 1]},  # 0=Off, 1=On
        'voice_control': {'id': 86, 'values': [0, 1]},  # 0=Off, 1=On
        'wake_on_voice': {'id': 104, 'values': [0, 1]},  # 0=Off, 1=On
        'wifi_band': {'id': 105, 'values': [0, 1]},  # 0=2.4GHz, 1=5GHz
    },
    'HERO11': {
        'anti_flicker': {'id': 134, 'values': [0, 1]},  # 0=60Hz, 1=50Hz
        'auto_power_down': {'id': 59, 'values': [0, 1, 2, 3, 4]},  # 0=Never, 1=1min, 2=5min, 3=15min, 4=30min
        'beep_volume': {'id': 87, 'values': [0, 40, 70, 100]},  # 0=Mute, 40=Low, 70=Medium, 100=High
        'video_format': {'id': 79, 'values': [9, 10, 11]},  # 9=HEVC, 10=H264+HEVC, 11=H264
        'video_resolution': {'id': 2, 'values': [1, 4, 9, 12, 18, 27]},  # Various resolutions
        'fps': {'id': 3, 'values': [1, 2, 5, 6, 8, 9, 10]},  # Various FPS values
        'lens': {'id': 121, 'values': [0, 4, 7]},  # Various lens modes
        'hypersmooth': {'id': 135, 'values': [0, 1, 2, 3]},  # 0=Off, 1=On, 2=High, 3=Boost
        'white_balance': {'id': 11, 'values': [0, 1, 2, 3, 4, 8]},  # Auto, 3000K, 4000K, 5500K, 6500K, Native
        'iso_max': {'id': 13, 'values': [0, 1, 2, 3, 4, 5]},  # 100, 200, 400, 800, 1600, 3200
        'iso_min': {'id': 102, 'values': [0, 1, 2, 3, 4]},  # 100, 200, 400, 800, 1600
        'sharpness': {'id': 14, 'values': [0, 1, 2]},  # Low, Medium, High
        'ev_comp': {'id': 15, 'values': [0, 1, 2, 3, 4, 5, 6, 7, 8]},  # -2.0 to +2.0
        'photo_resolution': {'id': 17, 'values': [12, 18, 27]},  # Various photo resolutions
        'raw_photo': {'id': 82, 'values': [0, 1]},  # 0=Off, 1=On
        'media_format': {'id': 128, 'values': [1]},  # 1=Format SD Card
        'camera_orientation': {'id': 52, 'values': [0, 1]},  # 0=Up, 1=Down
        'quick_capture': {'id': 54, 'values': [0, 1]},  # 0=Off, 1=On
        'led_status': {'id': 55, 'values': [0, 1, 2, 3, 4]},  # Off, Front Only, All On, Back Only, Front+Top
        'video_compression': {'id': 60, 'values': [0, 1]},  # 0=Standard (H.264), 1=High Efficiency (HEVC)
        'gps_status': {'id': 83, 'values': [0, 1]},  # 0=Off, 1=On
        'voice_control': {'id': 86, 'values': [0, 1]},  # 0=Off, 1=On
        'wake_on_voice': {'id': 104, 'values': [0, 1]},  # 0=Off, 1=On
        'wifi_band': {'id': 105, 'values': [0, 1]},  # 0=2.4GHz, 1=5GHz
    },
    'HERO10': {
        'anti_flicker': {'id': 134, 'values': [0, 1]},  # 0=60Hz, 1=50Hz
        'auto_power_down': {'id': 59, 'values': [0, 1, 2, 3, 4]},  # 0=Never, 1=1min, 2=5min, 3=15min, 4=30min
        'beep_volume': {'id': 87, 'values': [0, 40, 70, 100]},  # 0=Mute, 40=Low, 70=Medium, 100=High
        'video_format': {'id': 79, 'values': [9, 10, 11]},  # 9=HEVC, 10=H264+HEVC, 11=H264
        'video_resolution': {'id': 2, 'values': [1, 4, 9, 12, 18]},  # Various resolutions
        'fps': {'id': 3, 'values': [1, 2, 5, 6, 8, 9, 10]},  # Various FPS values
        'lens': {'id': 121, 'values': [0, 4, 7]},  # Various lens modes
        'hypersmooth': {'id': 135, 'values': [0, 1, 2]},  # 0=Off, 1=On, 2=High
        'white_balance': {'id': 11, 'values': [0, 1, 2, 3, 4]},  # Auto, 3000K, 4000K, 5500K, 6500K
        'iso_max': {'id': 13, 'values': [0, 1, 2, 3, 4]},  # 100, 200, 400, 800, 1600
        'iso_min': {'id': 102, 'values': [0, 1, 2, 3]},  # 100, 200, 400, 800
        'sharpness': {'id': 14, 'values': [0, 1, 2]},  # Low, Medium, High
        'ev_comp': {'id': 15, 'values': [0, 1, 2, 3, 4, 5, 6, 7, 8]},  # -2.0 to +2.0
        'photo_resolution': {'id': 17, 'values': [12, 18, 27]},  # Various photo resolutions
        'raw_photo': {'id': 82, 'values': [0, 1]},  # 0=Off, 1=On
        'media_format': {'id': 128, 'values': [1]},  # 1=Format SD Card
        'camera_orientation': {'id': 52, 'values': [0, 1]},  # 0=Up, 1=Down
        'quick_capture': {'id': 54, 'values': [0, 1]},  # 0=Off, 1=On
        'led_status': {'id': 55, 'values': [0, 1, 2, 3, 4]},  # Off, Front Only, All On, Back Only, Front+Top
        'video_compression': {'id': 60, 'values': [0, 1]},  # 0=Standard (H.264), 1=High Efficiency (HEVC)
        'gps_status': {'id': 83, 'values': [0, 1]},  # 0=Off, 1=On
        'voice_control': {'id': 86, 'values': [0, 1]},  # 0=Off, 1=On
        'wake_on_voice': {'id': 104, 'values': [0, 1]},  # 0=Off, 1=On
        'wifi_band': {'id': 105, 'values': [0, 1]},  # 0=2.4GHz, 1=5GHz
    }
}

def get_camera_model(camera_ip):
    """Determines the camera model by IP"""
    try:
        # Use the correct endpoint from the documentation
        url = f"http://{camera_ip}:8080/gp/gpControl/info"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            info = response.json()
            model_name = info.get("info", {}).get("model_name", "").upper()
            firmware = info.get("info", {}).get("firmware_version")
            
            logging.info(f"Camera info: Model={model_name}, Firmware={firmware}")
            
            # Determine the camera model
            if "HERO13" in model_name:
                return "HERO13"
            elif "HERO12" in model_name:
                return "HERO12"
            elif "HERO11" in model_name:
                return "HERO11"
            elif "HERO10" in model_name:
                return "HERO10"
            elif "HERO9" in model_name:
                return "HERO9"
        except requests.RequestException as e:
            logging.warning(f"Failed to get model via /gp/gpControl/info for {camera_ip}: {e}")
            
        # If it fails, try using the status endpoint
        url = f"http://{camera_ip}:8080/gp/gpControl/status"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        state = response.json()
        
        # Get the model from system information
        system_info = state.get("status", {})
        model_number = system_info.get("30", "")  # Field 30 contains the camera name
        
        # Determine the model by model number
        model_map = {
            "HD13": "HERO13",
            "HD12": "HERO12",
            "HD11": "HERO11",
            "HD10": "HERO10",
            "HD9": "HERO9"
        }
        
        for prefix, model in model_map.items():
            if prefix in model_number:
                return model
                
        logging.warning(f"Unknown camera model number: {model_number}")
        return None
        
    except Exception as e:
        logging.error(f"Failed to get camera model for {camera_ip}: {e}")
        return None

def is_setting_supported(setting_id, value, camera_model):
    """Checks if a setting is supported for the given camera model"""
    try:
        if camera_model not in CAMERA_SETTINGS:
            logging.warning(f"Camera model {camera_model} not found in supported settings")
            return False
        
        # Convert setting_id to int
        setting_id = int(setting_id)
        value = int(value)
        
        # Look for the setting by ID
        for setting_name, setting_info in CAMERA_SETTINGS[camera_model].items():
            if setting_info['id'] == setting_id:
                if value in setting_info['values']:
                    return True
                else:
                    logging.warning(
                        f"Value {value} not supported for setting {setting_name} "
                        f"(ID: {setting_id}) on {camera_model}. "
                        f"Supported values: {setting_info['values']}"
                    )
                    return False
                    
        logging.warning(f"Setting ID {setting_id} not found in supported settings for {camera_model}")
        return False
        
    except (ValueError, TypeError) as e:
        logging.error(f"Error checking setting support: {e}")
        return False

def check_camera_state(camera_ip):
    """Checks the state of the camera before applying settings"""
    try:
        url = f"http://{camera_ip}:8080/gp/gpControl/status"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        state = response.json()
        
        # Check the camera state
        status = state.get("status", {})
        settings = state.get("settings", {})
        
        # Log all important states for debugging
        logging.debug(f"Camera {camera_ip} full status: {json.dumps(status, indent=2)}")
        
        # Check various states
        is_recording = status.get("43", 0) == 1  # 43 = Recording state
        is_busy = status.get("8", 0) == 1        # 8 = System busy
        is_encoding = status.get("10", 0) == 1   # 10 = Encoding
        battery_level = status.get("2", 0)       # 2 = Battery level (for information only)
        
        # Log states
        logging.info(f"""
Camera {camera_ip} state:
- Recording: {is_recording}
- Busy: {is_busy}
- Encoding: {is_encoding}
- Battery: {battery_level}%
""")
        
        if is_recording:
            logging.warning(f"Camera {camera_ip} is recording")
            return False
        if is_busy:
            logging.warning(f"Camera {camera_ip} is busy")
            return False
        if is_encoding:
            logging.warning(f"Camera {camera_ip} is encoding")
            return False
            
        logging.info(f"Camera {camera_ip} is ready for settings")
        return True
        
    except Exception as e:
        logging.error(f"Failed to check camera state for {camera_ip}: {e}")
        return False

def check_copy_settings_dependencies():
    """Checks dependencies for copying settings"""
    required_files = [
        'prime_camera_sn.py',
        'goprolist_and_start_usb.py',
        'data/camera_cache.json'
    ]
    
    app_root = get_app_root()
    missing_files = []
    
    for file in required_files:
        if not (app_root / file).exists():
            missing_files.append(file)
    
    if missing_files:
        raise FileNotFoundError(f"Missing required files: {', '.join(missing_files)}")

def get_primary_camera_serial():
    try:
        prime_sn_path = get_app_root() / "prime_camera_sn.py"
        with open(prime_sn_path, "r") as file:
            for line in file:
                if "serial_number" in line:
                    return line.split("=")[1].strip().strip("\"')")
    except Exception as e:
        logging.error(f"Error reading primary camera config: {e}")
        return None

def copy_settings_to_camera(target_camera, settings, primary_model, progress_callback=None):
    """Copy settings to target camera"""
    try:
        target_ip = target_camera["ip"]
        
        if progress_callback:
            progress_callback("log", f"\nStarting settings copy to camera {target_ip}")
        
        # Get target camera model for logging
        target_model = get_camera_model(target_ip)
        if not target_model:
            error_msg = f"Failed to determine camera model for {target_ip}"
            logging.error(error_msg)
            if progress_callback:
                progress_callback("log", error_msg)
            return False
            
        if progress_callback:
            progress_callback("log", f"Camera model: {target_model}")
        
        # Check camera state
        if not check_camera_state(target_ip):
            error_msg = f"Camera {target_ip} is not ready for settings"
            logging.error(error_msg)
            if progress_callback:
                progress_callback("log", error_msg)
            return False
            
        status_text = f"Applying settings to {target_model} camera (IP: {target_ip})"
        logging.info(status_text)
        if progress_callback:
            progress_callback("status", status_text)
            progress_callback("log", f"\nTotal settings to copy: {len(settings)}")
        
        # Create session for connection reuse
        with requests.Session() as session:
            session.timeout = 5  # Set timeout
            
            # Get total settings count for progress
            total_settings = len(settings)
            current_setting = 0
            success_count = 0
            failed_count = 0
            
            # Apply all settings directly
            for setting_id, value in settings.items():
                try:
                    # Convert values to int
                    setting_id = int(setting_id)
                    value = int(value)
                    
                    # Update progress
                    current_setting += 1
                    if progress_callback:
                        progress_callback("log", f"\nSetting {current_setting}/{total_settings}:")
                        progress_callback("log", f"ID: {setting_id}, Value: {value}")
                        progress_callback("progress", (current_setting, total_settings))
                    
                    # Use correct endpoint for settings
                    set_url = f"http://{target_ip}:8080/gp/gpControl/setting/{setting_id}/{value}"
                    response = session.get(set_url)
                    
                    if response.status_code == 200:
                        success_count += 1
                        log_msg = f"✓ Successfully set"
                        logging.info(log_msg)
                        if progress_callback:
                            progress_callback("log", log_msg)
                    else:
                        failed_count += 1
                        log_msg = f"✗ Error: code {response.status_code}"
                        logging.warning(log_msg)
                        if progress_callback:
                            progress_callback("log", log_msg)
                        if response.status_code == 500:
                            log_msg = "Internal camera error - may need reboot"
                            logging.warning(log_msg)
                            if progress_callback:
                                progress_callback("log", log_msg)
                    
                    time.sleep(0.2)  # Increased delay between settings
                    
                except requests.RequestException as e:
                    failed_count += 1
                    log_msg = f"✗ Error setting {setting_id}: {e}"
                    logging.error(log_msg)
                    if progress_callback:
                        progress_callback("log", log_msg)
                    continue
                
                # Check state after each setting
                if not check_camera_state(target_ip):
                    log_msg = f"\n⚠ Camera {target_ip} stopped responding, aborting settings copy"
                    logging.error(log_msg)
                    if progress_callback:
                        progress_callback("log", log_msg)
                    return False
            
            # Output final statistics
            summary = f"""
\nSettings copy summary for camera {target_ip}:
✓ Successfully set: {success_count}
✗ Failed to set: {failed_count}
Total settings: {total_settings}
Success rate: {(success_count/total_settings)*100:.1f}%
"""
            logging.info(summary)
            if progress_callback:
                progress_callback("log", summary)
            
            return True
            
    except Exception as e:
        error_msg = f"Error copying settings to {target_ip}: {str(e)}"
        logging.error(error_msg)
        if progress_callback:
            progress_callback("log", f"\n❌ {error_msg}")
        return False

def copy_camera_settings(progress_callback=None):
    """Copy settings from prime camera to all other cameras"""
    try:
        if progress_callback:
            progress_callback("status", "Initializing...")
            progress_callback("progress", (0, 100))
            progress_callback("log", "Starting settings copy process...")
        
        # Get camera list
        if progress_callback:
            progress_callback("status", "Searching for cameras...")
            progress_callback("log", "Looking for connected cameras...")
            
        cameras = get_camera_list()
        if not cameras:
            error_msg = "No cameras found"
            if progress_callback:
                progress_callback("log", f"Error: {error_msg}")
            return False
            
        if progress_callback:
            progress_callback("log", f"Found {len(cameras)} cameras")
        
        # Find prime camera
        if progress_callback:
            progress_callback("status", "Looking for prime camera...")
            progress_callback("log", "Identifying prime camera...")
            
        prime_camera = None
        for camera in cameras:
            if is_prime_camera(camera):
                prime_camera = camera
                break
                
        if not prime_camera:
            error_msg = "Prime camera not found"
            if progress_callback:
                progress_callback("log", f"Error: {error_msg}")
            return False
            
        if progress_callback:
            progress_callback("log", f"Prime camera found: {prime_camera['ip']}")
            
        # Get prime camera settings
        if progress_callback:
            progress_callback("status", "Getting settings from prime camera...")
            progress_callback("log", "Reading current settings from prime camera...")
            
        prime_settings = get_camera_settings(prime_camera)
        if not prime_settings:
            error_msg = "Failed to get settings from prime camera"
            if progress_callback:
                progress_callback("log", f"Error: {error_msg}")
            return False
            
        if progress_callback:
            progress_callback("log", f"Retrieved {len(prime_settings)} settings")
            
        # Get prime camera model
        if progress_callback:
            progress_callback("status", "Determining prime camera model...")
            
        prime_model = get_camera_model(prime_camera['ip'])
        if not prime_model:
            error_msg = "Failed to determine prime camera model"
            if progress_callback:
                progress_callback("log", f"Error: {error_msg}")
            return False
            
        if progress_callback:
            progress_callback("log", f"Prime camera model: {prime_model}")
        
        # Copy settings to other cameras in parallel
        other_cameras = [c for c in cameras if not is_prime_camera(c)]
        total_cameras = len(other_cameras)
        
        if progress_callback:
            progress_callback("log", f"\nStarting parallel copy to {total_cameras} cameras...")
            progress_callback("status", "Copying settings to all cameras...")
        
        # Create thread pool for parallel execution
        with ThreadPoolExecutor(max_workers=total_cameras) as executor:
            # Start all copy operations
            futures = []
            for camera in other_cameras:
                future = executor.submit(
                    copy_settings_to_camera,
                    camera,
                    prime_settings,
                    prime_model,
                    progress_callback
                )
                futures.append(future)
            
            # Wait for all operations to complete
            completed_count = 0
            for future in futures:
                try:
                    if future.result():  # True if successful
                        completed_count += 1
                    if progress_callback:
                        progress = int((completed_count / total_cameras) * 100)
                        progress_callback("progress", (progress, 100))
                except Exception as e:
                    logging.error(f"Error in parallel copy: {e}")
        
        if progress_callback:
            progress_callback("progress", (100, 100))
            progress_callback("status", "Settings copied successfully")
            progress_callback("log", "\nSettings copy process completed")
            progress_callback("complete", None)
            
        return True
        
    except Exception as e:
        error_msg = f"Error copying settings: {str(e)}"
        logging.error(error_msg)
        if progress_callback:
            progress_callback("log", f"\n❌ {error_msg}")
        return False

def get_camera_list():
    """Gets the list of all connected cameras"""
    try:
        # Connect cameras via USB
        import goprolist_and_start_usb
        goprolist_and_start_usb.main()
        
        # Allow time for USB initialization
        time.sleep(2)
        
        # Retrieve the list of cameras
        devices = discover_gopro_devices()
        if not devices:
            logging.error("No GoPro devices found")
            return None
            
        logging.info(f"Found {len(devices)} cameras")
        return devices

    except Exception as e:
        logging.error(f"Error getting camera list: {e}")
        return None

def is_prime_camera(camera):
    """Checks if the camera is the primary one"""
    try:
        # Get the serial number of the primary camera
        prime_serial = get_primary_camera_serial()
        if not prime_serial:
            logging.error("Could not get primary camera serial number")
            return False
            
        # Get the serial number of the camera being checked
        url = f"http://{camera['ip']}:8080/gp/gpControl/info"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        info = response.json()
        camera_serial = info.get("info", {}).get("serial_number")
        
        # Compare serial numbers
        is_prime = prime_serial in str(camera_serial)
        if is_prime:
            logging.info(f"Found primary camera: {camera}")
        
        return is_prime
        
    except Exception as e:
        logging.error(f"Error checking if camera is primary: {e}")
        return False

def get_camera_settings(camera):
    """Gets the current settings of the camera"""
    try:
        url = f"http://{camera['ip']}:8080/gp/gpControl/status"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json().get("settings", {})
    except Exception as e:
        logging.error(f"Error getting camera settings: {e}")
        return None

def show_copy_progress_dialog(parent=None):
    """Show progress dialog for copying settings"""
    dialog = SettingsProgressDialog("Copying Camera Settings", copy_camera_settings, parent)
    dialog.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    show_copy_progress_dialog()
    sys.exit(app.exec_())
