import json
import logging
import requests
import time
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from utils import get_app_root, setup_logging
from read_and_write_all_settings_from_prime_to_other import (
    CAMERA_SETTINGS,
    get_camera_model,
    is_setting_supported,
    check_camera_state,
    copy_settings_to_camera
)
import os

# Mode prefixes for different camera modes
MODE_PREFIXES = {
    'video': 'video_',
    'photo': 'photo_',
    'timelapse': 'timelapse_'
}

@dataclass
class CameraPreset:
    name: str
    description: str
    settings: Dict
    created_at: str
    updated_at: str
    mode: str
    
class PresetManager:
    def __init__(self):
        # Use the same templates directory as the main application
        current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.templates_dir = current_dir / 'camera_templates'
        self.templates_dir.mkdir(exist_ok=True)
        logging.info(f"Templates directory: {self.templates_dir}")

    def get_preset_path(self, name: str, mode: str) -> Path:
        """Get full path for a preset file"""
        prefix = MODE_PREFIXES.get(mode.lower(), 'unknown_')
        return self.templates_dir / f"{prefix}{name}.json"

    def create_preset(self, name: str, camera_ip: str, mode: str = 'video', description: str = ''):
        """Creates a new preset from current camera settings"""
        try:
            # Get camera settings
            url = f"http://{camera_ip}:8080/gp/gpControl/status"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            camera_state = response.json()
            settings = camera_state.get("settings", {})
            
            # Get camera model
            camera_model = get_camera_model(camera_ip)
            if not camera_model:
                raise ValueError("Could not determine camera model")
            
            # Format settings
            formatted_settings = {}
            for setting_id, value in settings.items():
                if isinstance(setting_id, str) and setting_id.isdigit():
                    formatted_settings[int(setting_id)] = int(value)
                else:
                    formatted_settings[setting_id] = value
            
            # Create template data
            timestamp = datetime.now().isoformat()
            template_data = {
                "metadata": {
                    "camera_ip": camera_ip,
                    "camera_model": camera_model,
                    "scan_date": timestamp,
                    "description": description or f"Preset created from {camera_model} camera",
                    "mode": mode.lower()
                },
                "settings": formatted_settings
            }
            
            # Save template
            preset_path = self.get_preset_path(name, mode)
            with open(preset_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2)
            
            logging.info(f"Created preset '{name}' from camera {camera_ip} (model: {camera_model})")
            return True
            
        except Exception as e:
            logging.error(f"Error creating preset: {e}")
            return False

    def apply_preset_to_camera(self, preset_name: str, mode: str, camera_ip: str, progress_callback=None):
        """Applies a preset to the camera"""
        try:
            preset_path = self.get_preset_path(preset_name, mode)
            if not preset_path.exists():
                raise ValueError(f"Preset '{preset_name}' not found")

            # Load template
            with open(preset_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # Get camera model
            target_model = get_camera_model(camera_ip)
            if not target_model:
                raise ValueError(f"Could not determine model for camera {camera_ip}")

            # Check camera state
            if not check_camera_state(camera_ip):
                raise ValueError(f"Camera {camera_ip} is busy or recording")

            settings = template_data.get("settings", {})
            source_model = template_data.get("metadata", {}).get("camera_model")

            if progress_callback:
                progress_callback("status", f"Applying preset '{preset_name}' to camera {camera_ip}")
                progress_callback("log", f"Source model: {source_model}, Target model: {target_model}")
            
            logging.info(f"Applying preset '{preset_name}' to {target_model} camera at {camera_ip}")
            
            # Create camera object
            target_camera = {
                "ip": camera_ip,
                "name": f"Camera_{camera_ip}"
            }
            
            # Apply settings
            copy_settings_to_camera(target_camera, settings, source_model, progress_callback)
            return True
            
        except Exception as e:
            error_msg = f"Error applying preset: {e}"
            logging.error(error_msg)
            if progress_callback:
                progress_callback("log", error_msg)
            return False

    def delete_preset(self, name: str, mode: str) -> bool:
        """Deletes a preset"""
        try:
            preset_path = self.get_preset_path(name, mode)
            if preset_path.exists():
                preset_path.unlink()
                logging.info(f"Deleted preset '{name}'")
                return True
            return False
        except Exception as e:
            logging.error(f"Error deleting preset: {e}")
            return False

    def get_preset_list(self, mode: Optional[str] = None) -> List[Dict]:
        """Returns list of available presets"""
        presets = []
        try:
            # Get all JSON files in templates directory
            if mode:
                prefix = MODE_PREFIXES.get(mode.lower(), '')
                pattern = f"{prefix}*.json"
            else:
                pattern = "*.json"
                
            for preset_file in self.templates_dir.glob(pattern):
                try:
                    with open(preset_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Get preset mode from filename
                    preset_mode = 'unknown'
                    for mode_key, prefix in MODE_PREFIXES.items():
                        if preset_file.name.startswith(prefix):
                            preset_mode = mode_key
                            break
                    
                    # Get name without prefix
                    name = preset_file.stem
                    for prefix in MODE_PREFIXES.values():
                        if name.startswith(prefix):
                            name = name[len(prefix):]
                            break
                    
                    presets.append({
                        'name': name,
                        'mode': preset_mode,
                        'description': data.get('metadata', {}).get('description', ''),
                        'created_at': data.get('metadata', {}).get('scan_date', ''),
                        'camera_model': data.get('metadata', {}).get('camera_model', ''),
                        'settings_count': len(data.get('settings', {}))
                    })
                except Exception as e:
                    logging.error(f"Error reading preset {preset_file}: {e}")
                    
            return sorted(presets, key=lambda x: x['name'])
            
        except Exception as e:
            logging.error(f"Error getting preset list: {e}")
            return []

    def get_preset_settings(self, name: str, mode: str) -> Optional[Dict]:
        """Returns preset settings"""
        try:
            preset_path = self.get_preset_path(name, mode)
            if preset_path.exists():
                with open(preset_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('settings', {})
            return None
        except Exception as e:
            logging.error(f"Error getting preset settings: {e}")
            return None

def get_camera_settings(camera_ip: str) -> Optional[Dict]:
    """Get current camera settings"""
    try:
        url = f"http://{camera_ip}:8080/gopro/camera/state"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json().get("settings", {})
    except Exception as e:
        logging.error(f"Error getting camera settings: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    preset_manager = PresetManager()
    
    # Create preset from current camera settings
    camera_ip = "10.5.5.9"  # Default GoPro camera IP
    settings = get_camera_settings(camera_ip)
    if settings:
        preset_manager.create_preset(
            name="default_4k",
            camera_ip=camera_ip
        )
    
    # Apply preset to camera
    preset = preset_manager.get_preset_settings("default_4k")
    if preset:
        preset_manager.apply_preset_to_camera("default_4k", "video", camera_ip) 