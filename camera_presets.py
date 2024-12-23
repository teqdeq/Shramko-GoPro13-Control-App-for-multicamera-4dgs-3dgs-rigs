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

@dataclass
class CameraPreset:
    name: str
    description: str
    settings: Dict
    created_at: str
    updated_at: str
    
class PresetManager:
    def __init__(self):
        self.presets_file = get_app_root() / "data" / "presets.json"
        self.presets_file.parent.mkdir(exist_ok=True)
        self.load_presets()

    def load_presets(self):
        """Загружает пресеты из файла"""
        try:
            if self.presets_file.exists():
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    self.presets = json.load(f)
            else:
                self.presets = {}
                self.save_presets()
        except Exception as e:
            logging.error(f"Error loading presets: {e}")
            self.presets = {}

    def save_presets(self):
        """Сохраняет пресеты в файл"""
        try:
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.presets, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving presets: {e}")

    def create_preset(self, name, camera_ip):
        """Создает новый пресет из текущих настроек камеры"""
        try:
            url = f"http://{camera_ip}:8080/gp/gpControl/status"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            camera_state = response.json()
            settings = camera_state.get("settings", {})
            
            # Получаем модель камеры
            camera_model = get_camera_model(camera_ip)
            if not camera_model:
                raise ValueError("Could not determine camera model")
            
            # Преобразуем настройки в нужный формат
            formatted_settings = {}
            for setting_id, value in settings.items():
                if isinstance(setting_id, str) and setting_id.isdigit():
                    formatted_settings[int(setting_id)] = int(value)
                else:
                    formatted_settings[setting_id] = value
                
            # Сохраняем все настройки без фильтрации
            self.presets[name] = {
                "settings": formatted_settings,
                "source_model": camera_model,
                "created_at": datetime.now().isoformat(),
                "description": f"Preset created from {camera_model} camera"
            }
            self.save_presets()
            logging.info(f"Created preset '{name}' from camera {camera_ip} (model: {camera_model})")
            return True
        except Exception as e:
            logging.error(f"Error creating preset: {e}")
            return False

    def apply_preset_to_camera(self, preset_name, camera_ip, progress_callback=None):
        """Применяет пресет к камере с учетом совместимости"""
        try:
            if preset_name not in self.presets:
                raise ValueError(f"Preset '{preset_name}' not found")

            # Получаем модель целевой камеры
            target_model = get_camera_model(camera_ip)
            if not target_model:
                raise ValueError(f"Could not determine model for camera {camera_ip}")

            # Проверяем состояние камеры
            if not check_camera_state(camera_ip):
                raise ValueError(f"Camera {camera_ip} is busy or recording")

            preset_data = self.presets[preset_name]
            settings = preset_data["settings"]
            source_model = preset_data.get("source_model")

            if progress_callback:
                progress_callback("status", f"Applying preset '{preset_name}' to camera {camera_ip}")
                progress_callback("log", f"Source model: {source_model}, Target model: {target_model}")
            
            logging.info(f"Applying preset '{preset_name}' to {target_model} camera at {camera_ip}")
            
            # Создаем объект камеры для функции copy_settings_to_camera
            target_camera = {
                "ip": camera_ip,
                "name": f"Camera_{camera_ip}"  # Временное имя
            }
            
            # Используем функцию из read_and_write_all_settings_from_prime_to_other.py
            copy_settings_to_camera(target_camera, settings, source_model, progress_callback)
            
            return True
            
        except Exception as e:
            error_msg = f"Error applying preset: {e}"
            logging.error(error_msg)
            if progress_callback:
                progress_callback("log", error_msg)
            return False

    def delete_preset(self, name):
        """Удаляет пресет"""
        try:
            if name in self.presets:
                del self.presets[name]
                self.save_presets()
                logging.info(f"Deleted preset '{name}'")
                return True
            return False
        except Exception as e:
            logging.error(f"Error deleting preset: {e}")
            return False

    def get_preset_list(self):
        """Возвращает список доступных пресетов"""
        return list(self.presets.keys())

    def get_preset_settings(self, name):
        """Возвращает настройки пресета"""
        return self.presets.get(name, {}).get("settings", {})

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
        preset_manager.apply_preset_to_camera("default_4k", camera_ip) 