__all__ = ['get_camera_settings', 'get_primary_camera_serial', 'is_prime_camera', 'copy_camera_settings_sync', 'USB_HEADERS', 'wait_for_camera_ready', 'get_camera_status']

import logging
import json
import requests
from datetime import datetime
import os
from goprolist_and_start_usb import discover_gopro_devices
from pathlib import Path
import time
from utils import get_app_root, setup_logging
import sys
from PyQt5.QtWidgets import QApplication
from progress_dialog import SettingsProgressDialog
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

# Logging setup
setup_logging()
logger = logging.getLogger(__name__)

# Main functions used by other modules
def get_primary_camera_serial():
    """Get the serial number of the primary camera"""
    try:
        prime_sn_path = get_app_root() / "prime_camera_sn.py"
        with open(prime_sn_path, "r") as file:
            for line in file:
                if "serial_number" in line:
                    return line.split("=")[1].strip().strip("\"')")
    except Exception as e:
        logger.error(f"Error reading primary camera config: {e}")
        return None

def get_camera_settings(camera_ip):
    """Retrieve camera settings"""
    try:
        url = f"http://{camera_ip}:8080/gp/gpControl/info"
        logger.debug(f"Getting settings from URL: {url}")
        logger.debug(f"Using headers: {USB_HEADERS}")
        
        response = requests.get(url, headers=USB_HEADERS, timeout=5)
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response content: {response.text[:200]}...")  # Log the first 200 characters of the response
        
        response.raise_for_status()
        info = response.json()
        settings = info.get("settings", {})
        logger.info(f"Got {len(settings)} settings from camera {camera_ip}")
        logger.debug(f"Settings: {settings}")
        return settings
    except Exception as e:
        logger.error(f"Failed to get settings from camera {camera_ip}: {e}")
        return None

def is_prime_camera(camera):
    """Check if the camera is the primary one"""
    try:
        prime_serial = get_primary_camera_serial()
        if not prime_serial:
            logger.error("Could not get primary camera serial number")
            return False
            
        url = f"http://{camera['ip']}:8080/gp/gpControl/info"
        response = requests.get(url, headers=USB_HEADERS, timeout=5)
        response.raise_for_status()
        info = response.json()
        camera_serial = info.get("info", {}).get("serial_number")
        
        is_prime = prime_serial in str(camera_serial)
        if is_prime:
            logger.info(f"Found primary camera: {camera}")
        
        return is_prime
        
    except Exception as e:
        logger.error(f"Error checking if camera is primary: {e}")
        return False

# Constants and settings
DELAYS = {
    'standard': 0.1,    # 100ms between regular settings
    'mode': 0.25,       # 250ms after changing mode
    'performance': 0.5  # 500ms after changing Performance Mode
}

# Priority settings for GoPro 13
SETTING_PRIORITIES = {
    'system': [
        '173',  # Performance Mode - must be first
        '126',  # System Mode - second
        '128'   # Media Format - third
    ],
    'core': [
        '2',    # Resolution
        '3',    # FPS 
        '91'    # Lens
    ],
    'features': [
        '135',  # HyperSmooth
        '64',   # Bitrate
        '115'   # Color
    ],
    'optional': []  # Add group for optional settings
}

# Settings dependency map
SETTING_DEPENDENCIES = {
    '2': ['126', '173'],     # Resolution depends on System Mode and Performance Mode
    '3': ['2', '173'],       # FPS depends on Resolution and Performance Mode
    '135': ['2', '3', '173'] # HyperSmooth depends on Resolution, FPS, and Performance Mode
}

# HTTP headers for USB connection
USB_HEADERS = {
    'Connection': 'Keep-Alive',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'User-Agent': 'GoPro-Control/1.0',
    'Cache-Control': 'no-cache'
}

def create_setting_checkpoint(camera_ip):
    """Create a settings checkpoint"""
    try:
        url = f"http://{camera_ip}:8080/gp/gpControl/setting/checkpoint"
        response = requests.post(url, headers=USB_HEADERS, timeout=5)
        if response.status_code == 200:
            checkpoint_id = response.json().get('checkpoint_id')
            logger.info(f"Created settings checkpoint: {checkpoint_id}")
            return checkpoint_id
        return None
    except Exception as e:
        logger.error(f"Failed to create checkpoint: {e}")
        return None

def restore_setting_checkpoint(camera_ip, checkpoint_id):
    """Restore settings from a checkpoint"""
    try:
        url = f"http://{camera_ip}:8080/gp/gpControl/setting/restore/{checkpoint_id}"
        response = requests.get(url, headers=USB_HEADERS, timeout=5)
        if response.status_code == 200:
            logger.info(f"Restored settings from checkpoint: {checkpoint_id}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to restore checkpoint: {e}")
        return False

def check_camera_health(camera_ip):
    """Check camera settings health"""
    try:
        url = f"http://{camera_ip}:8080/gp/gpControl/setting/health"
        response = requests.get(url, headers=USB_HEADERS, timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            settings_status = health_data.get('settings_status', {})
            
            # Check the status of each setting
            mismatched_settings = []
            for setting_id, status in settings_status.items():
                if status['status'] != 'ok':
                    mismatched_settings.append({
                        'id': setting_id,
                        'expected': status['expected'],
                        'current': status['value'],
                        'last_set': status.get('last_set', 'unknown'),
                        'status': status['status']
                    })
            
            if mismatched_settings:
                logger.warning(f"Found {len(mismatched_settings)} mismatched settings")
                return False, mismatched_settings
            
            logger.debug("Settings health check passed")
            return True, []
            
    except Exception as e:
        logger.error(f"Failed to check camera health: {e}")
        return False, []

def validate_settings_batch(camera_ip, settings):
    """Validate a batch of settings before applying"""
    try:
        # Apply settings directly without validation
        success = True
        for setting_id, value in settings.items():
            url = f"http://{camera_ip}:8080/gp/gpControl/setting/{setting_id}/{value}"
            logger.debug(f"Setting {setting_id}={value} on camera {camera_ip}")
            
            response = requests.get(url, headers=USB_HEADERS, timeout=5)
            if response.status_code != 200:
                logger.error(f"Failed to set {setting_id}={value}. Status: {response.status_code}")
                success = False
                break
                
            # Verify the setting application
            if not verify_setting(camera_ip, setting_id, value):
                success = False
                break
                
            # Give the camera time to apply
            time.sleep(DELAYS['standard'])
            
        return (success, [])
        
    except Exception as e:
        logger.error(f"Failed to apply settings: {e}")
        return None

def validate_settings(camera_ip, settings):
    """Validate settings before applying"""
    try:
        url = f"http://{camera_ip}:8080/gp/gpControl/setting/validate"
        payload = {
            "settings": settings
        }
        
        response = requests.get(url, json=payload, headers=USB_HEADERS, timeout=5)
        if response.status_code == 200:
            validation_result = response.json()
            if validation_result.get('valid'):
                logger.debug(f"Settings validation successful for camera {camera_ip}")
                return True, None
            else:
                conflicts = validation_result.get('conflicts', [])
                logger.warning(f"Settings validation failed: {conflicts}")
                return False, conflicts
        else:
            logger.error(f"Validation request failed: {response.status_code}")
            return False, None
            
    except Exception as e:
        logger.error(f"Error during settings validation: {e}")
        return False, None

def handle_response_code(response, setting_id, value):
    """Handle response codes from the camera"""
    if response.status_code == 200:
        logger.debug(f"Successfully applied setting {setting_id}={value}")
        return True
    elif response.status_code == 403:
        supported_values = response.json().get('supported_values', [])
        logger.error(f"Invalid value {value} for setting {setting_id}. Supported values: {supported_values}")
        return False
    elif response.status_code == 409:
        logger.error(f"Setting conflict for {setting_id}={value}")
        return False
    elif response.status_code == 500:
        logger.error(f"Camera error while setting {setting_id}={value}")
        return False
    else:
        logger.error(f"Unexpected response code {response.status_code} for setting {setting_id}")
        return False

def apply_setting(camera_ip, setting_id, value):
    """Apply a single setting"""
    try:
        # First check the current value
        status_url = f"http://{camera_ip}:8080/gp/gpControl/status"
        status_response = requests.get(status_url, headers=USB_HEADERS, timeout=5)
        if status_response.status_code == 200:
            current_value = status_response.json().get('settings', {}).get(str(setting_id))
            if current_value == value:
                logger.debug(f"Setting {setting_id} already has value {value}")
                return True

        # Apply the setting
        url = f"http://{camera_ip}:8080/gp/gpControl/setting/{setting_id}/{value}"
        logger.debug(f"Applying setting {setting_id}={value} to camera {camera_ip}")
        
        response = requests.get(url, headers=USB_HEADERS, timeout=5)
        if not handle_response_code(response, setting_id, value):
            return False
            
        # Choose the correct delay depending on the type of setting
        if setting_id == '173':  # Performance Mode
            delay = DELAYS['performance']
        elif setting_id in ['126', '128']:  # System Mode and Media Format
            delay = DELAYS['mode']
        else:
            delay = DELAYS['standard']
            
        time.sleep(delay)
        
        # Verify the application
        verify_response = requests.get(status_url, headers=USB_HEADERS, timeout=5)
        if verify_response.status_code == 200:
            new_value = verify_response.json().get('settings', {}).get(str(setting_id))
            if new_value == value:
                return True
                
        logger.error(f"Failed to verify setting {setting_id}={value}")
        return False
        
    except Exception as e:
        logger.error(f"Error applying setting {setting_id}: {e}")
        return False

def get_settings_conflicts(camera_ip):
    """Get the settings conflict matrix"""
    try:
        url = f"http://{camera_ip}:8080/gp/gpControl/setting/conflicts"
        response = requests.get(url, headers=USB_HEADERS, timeout=5)
        if response.status_code == 200:
            return response.json()
        logger.error(f"Failed to get conflicts matrix. Status: {response.status_code}")
        return None
    except Exception as e:
        logger.error(f"Error getting conflicts matrix: {e}")
        return None

def check_settings_conflicts(camera_ip, settings_batch):
    """Check conflicts in a batch of settings"""
    try:
        conflicts_matrix = get_settings_conflicts(camera_ip)
        if not conflicts_matrix:
            logger.warning("Could not get conflicts matrix, skipping conflict check")
            return True, None
            
        # Check conflicts between settings in the batch
        found_conflicts = []
        for setting_id, value in settings_batch.items():
            # Check conflicts with other settings
            if setting_id in conflicts_matrix:
                conflicting_settings = conflicts_matrix[setting_id]
                for conflict_id, conflict_rules in conflicting_settings.items():
                    if conflict_id in settings_batch:
                        # Check if the values conflict
                        if not is_valid_combination(
                            value, 
                            settings_batch[conflict_id],
                            conflict_rules
                        ):
                            found_conflicts.append({
                                'setting_id': setting_id,
                                'value': value,
                                'conflicts_with': {
                                    'setting_id': conflict_id,
                                    'value': settings_batch[conflict_id],
                                    'rules': conflict_rules
                                }
                            })
                            
        if found_conflicts:
            logger.error(f"Found setting conflicts: {found_conflicts}")
            return False, found_conflicts
            
        return True, None
        
    except Exception as e:
        logger.error(f"Error checking settings conflicts: {e}")
        return False, None

def is_valid_combination(value1, value2, rules):
    """Check the validity of a combination of setting values"""
    try:
        # Rules can be in different formats, handle the main cases
        if isinstance(rules, dict):
            if 'invalid_combinations' in rules:
                # Check if the combination is in the list of invalid combinations
                return (value1, value2) not in rules['invalid_combinations']
            elif 'valid_combinations' in rules:
                # Check if the combination is in the list of valid combinations
                return (value1, value2) in rules['valid_combinations']
        return True  # If the format of the rules is unknown, consider the combination valid
    except Exception as e:
        logger.error(f"Error checking value combination: {e}")
        return True

def apply_settings_batch(camera_ip, settings_batch):
    """Apply a batch of settings in strict priority order"""
    try:
        # Group settings by priority
        grouped = group_settings_by_priority(settings_batch)
        
        # Apply settings strictly in order
        priority_groups = ['system', 'core', 'features', 'optional']
        
        for group in priority_groups:
            if not grouped[group]:
                continue
                
            logger.info(f"Applying {group} settings...")
            
            # For system settings, apply in strict order
            if group == 'system':
                for setting_id in SETTING_PRIORITIES['system']:
                    if setting_id in grouped['system']:
                        value = grouped['system'][setting_id]
                        if not apply_setting(camera_ip, setting_id, value):
                            logger.error(f"Failed to apply system setting {setting_id}")
                            return False
                        # Increased delay after system settings
                        time.sleep(DELAYS['mode'])
            else:
                # For other groups, apply in batches
                current_batch = grouped[group]
                if not apply_settings_group(camera_ip, current_batch):
                    return False
                    
            # Check status after each group
            if not wait_for_camera_ready(camera_ip):
                logger.error(f"Camera not ready after applying {group} settings")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply settings batch: {e}")
        return False

def apply_settings_group(camera_ip, settings_group, max_batch_size=10):
    """Apply a group of settings in batches"""
    try:
        batch = {}
        count = 0
        
        for setting_id, value in settings_group.items():
            batch[setting_id] = value
            count += 1
            
            if count >= max_batch_size:
                if not apply_batch(camera_ip, batch):
                    return False
                batch = {}
                count = 0
                
        # Apply remaining settings
        if batch:
            if not apply_batch(camera_ip, batch):
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Error applying settings group: {e}")
        return False

def apply_batch(camera_ip, batch):
    """Apply a single batch of settings"""
    try:
        for setting_id, value in batch.items():
            if not apply_setting(camera_ip, setting_id, value):
                return False
                
        # Check status after the batch
        if not wait_for_camera_ready(camera_ip):
            time.sleep(0.5)  # Additional delay if the camera is busy
            
        return True
        
    except Exception as e:
        logger.error(f"Error applying batch: {e}")
        return False

def get_camera_status(camera_ip):
    """Get the full status of the camera"""
    try:
        url = f"http://{camera_ip}:8080/gopro/camera/state"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        logger.error(f"Failed to get camera status. Status code: {response.status_code}")
        return None
    except Exception as e:
        logger.error(f"Error getting camera status: {str(e)}")
        return None

def group_settings_by_priority(settings):
    """Group settings by priority"""
    grouped = {
        'system': {},
        'core': {},
        'features': {},
        'optional': {}  # Add optional group
    }
    
    for setting_id, value in settings.items():
        if setting_id in SETTING_PRIORITIES['system']:
            grouped['system'][setting_id] = value
        elif setting_id in SETTING_PRIORITIES['core']:
            grouped['core'][setting_id] = value
        elif setting_id in SETTING_PRIORITIES['features']:
            grouped['features'][setting_id] = value
        else:
            grouped['optional'][setting_id] = value  # All other settings go to optional
            
    return grouped

def check_setting_dependencies(setting_id, settings):
    """Check setting dependencies"""
    if setting_id in SETTING_DEPENDENCIES:
        for dep_id in SETTING_DEPENDENCIES[setting_id]:
            if dep_id not in settings:
                logger.warning(f"Missing dependency {dep_id} for setting {setting_id}")
                return False
    return True

def create_settings_batches(settings, batch_size=1):
    """Create batches of settings considering dependencies"""
    batches = []
    
    # First system settings
    system_settings = {k: v for k, v in settings.items() 
                      if k in SETTING_PRIORITIES['system']}
    if system_settings:
        for k, v in system_settings.items():
            if check_setting_dependencies(k, settings):
                batches.append({k: v})
    
    # Then core settings
    core_settings = {k: v for k, v in settings.items() 
                    if k in SETTING_PRIORITIES['core']}
    if core_settings:
        for k, v in core_settings.items():
            if check_setting_dependencies(k, settings):
                batches.append({k: v})
    
    # Other settings
    other_settings = {k: v for k, v in settings.items() 
                     if k not in SETTING_PRIORITIES['system'] 
                     and k not in SETTING_PRIORITIES['core']}
    if other_settings:
        for k, v in other_settings.items():
            if check_setting_dependencies(k, settings):
                batches.append({k: v})
    
    return batches

def wait_for_camera_ready(camera_ip, timeout=5):
    """Wait for the camera to be ready"""
    try:
        start_time = time.time()
        while time.time() - start_time < timeout:
            url = f"http://{camera_ip}:8080/gp/gpControl/status"
            response = requests.get(url, headers=USB_HEADERS, timeout=2)
            
            if response.status_code == 200:
                status = response.json()
                # Check main busy flags
                system_busy = status.get('status', {}).get('8', 0) == 1  # system busy
                encoding = status.get('status', {}).get('10', 0) == 1    # encoding
                
                if not (system_busy or encoding):
                    logger.debug(f"Camera {camera_ip} is ready")
                    return True
                    
            time.sleep(0.2)
            
        logger.warning(f"Camera {camera_ip} ready timeout after {timeout}s")
        return False
        
    except Exception as e:
        logger.error(f"Error checking camera ready state: {e}")
        return False

def copy_camera_settings_sync(progress_callback=None):
    """Copy settings from the primary camera to others"""
    try:
        # Get the list of cameras
        cameras = discover_gopro_devices()
        if not cameras:
            error_msg = "No cameras found"
            logger.error(error_msg)
            if progress_callback:
                progress_callback("log", f"❌ {error_msg}")
            return False

        # Find the primary camera
        primary_camera = None
        for camera in cameras:
            if is_prime_camera(camera):
                primary_camera = camera
                break

        if not primary_camera:
            error_msg = "Primary camera not found"
            logger.error(error_msg)
            if progress_callback:
                progress_callback("log", f"❌ {error_msg}")
            return False

        # Get settings from the primary camera
        primary_status = get_camera_status(primary_camera['ip'])
        if not primary_status:
            error_msg = "Failed to get primary camera status"
            logger.error(error_msg)
            if progress_callback:
                progress_callback("log", f"❌ {error_msg}")
            return False

        current_settings = primary_status.get('settings', {})
        if not current_settings:
            error_msg = "No settings found in primary camera"
            logger.error(error_msg)
            if progress_callback:
                progress_callback("log", f"❌ {error_msg}")
            return False

        # Group settings by priority
        grouped_settings = group_settings_by_priority(current_settings)
        
        # Copy settings to other cameras
        for camera in cameras:
            if is_prime_camera(camera):
                continue
                
            if progress_callback:
                progress_callback("log", f"\nProcessing camera {camera['ip']}")
                
            # Check camera readiness
            if not wait_for_camera_ready(camera['ip']):
                logger.error(f"Camera {camera['ip']} not ready")
                continue
                
            try:
                # Apply settings strictly in order
                for priority_group in SETTING_PRIORITIES:
                    settings_ids = SETTING_PRIORITIES[priority_group]
                    
                    if progress_callback:
                        progress_callback("log", f"\nApplying {priority_group} settings...")
                        
                    # Apply settings in the specified order
                    for setting_id in settings_ids:
                        if setting_id not in current_settings:
                            continue
                            
                        value = current_settings[setting_id]
                        retry_count = 0
                        max_retries = 3
                        
                        while retry_count < max_retries:
                            if apply_setting(camera['ip'], setting_id, value):
                                if progress_callback:
                                    progress_callback("log", f"✅ Set {setting_id}={value}")
                                break
                                
                            retry_count += 1
                            if retry_count < max_retries:
                                time.sleep(DELAYS['performance'])
                                
                        if retry_count >= max_retries:
                            logger.error(f"Failed to set {setting_id} after {max_retries} attempts")
                            if progress_callback:
                                progress_callback("log", f"❌ Failed to set {setting_id}")
                                
                    # Give the camera time to apply the group of settings
                    time.sleep(DELAYS['mode'])
                    
                # Apply other settings
                for setting_id, value in current_settings.items():
                    if any(setting_id in group for group in SETTING_PRIORITIES.values()):
                        continue
                        
                    if apply_setting(camera['ip'], setting_id, value):
                        if progress_callback:
                            progress_callback("log", f"✅ Set {setting_id}={value}")
                            
            except Exception as e:
                logger.error(f"Error applying settings to camera {camera['ip']}: {e}")
                continue
                    
        return True
        
    except Exception as e:
        logger.error(f"Error copying settings: {e}")
        return False

def verify_setting(camera_ip, setting_id, expected_value):
    """Verify the application of a setting"""
    try:
        url = f"http://{camera_ip}:8080/gp/gpControl/status"
        response = requests.get(url, headers=USB_HEADERS, timeout=5)
        
        if response.status_code == 200:
            status = response.json()
            current_value = status.get('settings', {}).get(setting_id)
            
            if current_value == expected_value:
                return True
                
            logger.warning(f"Setting verification failed: expected {expected_value}, got {current_value}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to verify setting: {e}")
        return False

def get_usb_connection_status(camera_ip):
    """Check the USB connection status"""
    try:
        url = f"http://{camera_ip}:8080/gp/gpControl/usb/status"
        response = requests.get(url, headers=USB_HEADERS, timeout=5)
        if response.status_code == 200:
            status = response.json()
            if status['connection'] == 'active':
                logger.debug(f"USB connection active for {camera_ip}")
                logger.debug(f"Bandwidth: {status.get('bandwidth')}MB/s")
                return True
            else:
                logger.warning(f"USB connection inactive for {camera_ip}")
                return False
    except Exception as e:
        logger.error(f"Failed to check USB connection: {e}")
        return False

@dataclass
class CameraResult:
    """Result of applying settings to a camera"""
    camera_ip: str
    success: bool
    settings_applied: Dict[str, bool]
    error_message: Optional[str] = None

class CameraSettingsManager:
    def __init__(self, max_concurrent_cameras: int = 50):
        self.semaphore = asyncio.Semaphore(max_concurrent_cameras)
        self.session: Optional[aiohttp.ClientSession] = None
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent_cameras)
        
    async def init_session(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=USB_HEADERS)

    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            
    async def verify_setting_async(self, camera_ip: str, setting_id: str, expected_value: Any) -> bool:
        """Asynchronous verification of a setting application"""
        try:
            url = f"http://{camera_ip}:8080/gp/gpControl/status"
            async with self.session.get(url) as response:
                if response.status == 200:
                    status = await response.json()
                    current_value = status.get('settings', {}).get(setting_id)
                    return current_value == expected_value
                return False
        except Exception as e:
            logger.error(f"Failed to verify setting: {e}")
            return False

    async def apply_setting_async(
        self, 
        camera_ip: str, 
        setting_id: str, 
        value: Any,
        progress_callback: Callable
    ) -> bool:
        """Asynchronous application of a single setting"""
        try:
            url = f"http://{camera_ip}:8080/gp/gpControl/setting/{setting_id}/{value}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    # Verify the setting application
                    if await self.verify_setting_async(camera_ip, setting_id, value):
                        progress_callback("log", f"✅ Camera {camera_ip}: Set {setting_id}={value}")
                        return True
                    else:
                        progress_callback("log", f"⚠️ Camera {camera_ip}: Setting {setting_id}={value} verification failed")
                        return False
                else:
                    progress_callback("log", f"❌ Camera {camera_ip}: Failed to set {setting_id}={value} (Status: {response.status})")
                    return False
        except Exception as e:
            progress_callback("log", f"❌ Camera {camera_ip}: Error setting {setting_id}={value}: {str(e)}")
            return False

    async def apply_settings_to_camera(
        self, 
        camera_ip: str, 
        settings: Dict[str, Any],
        progress_callback: Callable
    ) -> CameraResult:
        """Apply all settings to a single camera"""
        async with self.semaphore:
            try:
                result = CameraResult(
                    camera_ip=camera_ip,
                    success=True,
                    settings_applied={}
                )

                # Group settings by priority
                grouped_settings = group_settings_by_priority(settings)
                
                # Apply settings by groups
                for priority_group in ['system', 'core', 'features', 'optional']:
                    if priority_group not in grouped_settings:
                        continue
                        
                    progress_callback("log", f"\nCamera {camera_ip}: Applying {priority_group} settings...")
                    
                    for setting_id, value in grouped_settings[priority_group].items():
                        success = await self.apply_setting_async(camera_ip, setting_id, value, progress_callback)
                        result.settings_applied[setting_id] = success
                        
                        if not success:
                            result.success = False
                        
                        # Apply delays
                        if priority_group == 'system':
                            await asyncio.sleep(DELAYS['mode'])
                        else:
                            await asyncio.sleep(DELAYS['standard'])
                
                return result
                
            except Exception as e:
                error_msg = f"Error applying settings to camera {camera_ip}: {str(e)}"
                logger.error(error_msg)
                return CameraResult(
                    camera_ip=camera_ip,
                    success=False,
                    settings_applied={},
                    error_message=error_msg
                )

    async def apply_settings_to_all_cameras(
        self,
        cameras: List[Dict[str, str]],
        settings: Dict[str, Any],
        progress_callback: Callable
    ) -> List[CameraResult]:
        """Asynchronous application of settings to all cameras"""
        await self.init_session()
        try:
            tasks = []
            for camera in cameras:
                task = self.apply_settings_to_camera(
                    camera_ip=camera['ip'],
                    settings=settings,
                    progress_callback=progress_callback
                )
                tasks.append(task)
            
            return await asyncio.gather(*tasks)
            
        finally:
            await self.close_session()

    @classmethod
    def apply_settings_sync(
        cls,
        cameras: List[Dict[str, str]],
        settings: Dict[str, Any],
        progress_callback: Callable
    ) -> List[CameraResult]:
        """Synchronous wrapper for asynchronous settings application"""
        async def _run():
            manager = cls()
            return await manager.apply_settings_to_all_cameras(cameras, settings, progress_callback)
            
        return asyncio.run(_run())

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        dialog = SettingsProgressDialog(
            "Copying Camera Settings",
            copy_camera_settings_sync,
            None
        )
        dialog.exec_()
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)