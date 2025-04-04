import os
from pathlib import Path
from typing import Dict, Any, Optional
from utils import load_json, save_json, get_data_dir, logger

class AppConfig:
    """Class for managing application configuration"""
    
    def __init__(self):
        self.data_dir = get_data_dir()
        self.config_file = self.data_dir / 'config.json'
        self.config: Dict[str, Any] = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            'camera_settings': {
                'default_preset': 0,
                'default_video_mode': 'standard',
                'orientation_lock': False
            },
            'copy_settings': {
                'scene_sorting': True,
                'verify_copies': True,
                'backup_enabled': False,
                'backup_path': str(Path.home() / 'GoPro_Backup')
            },
            'sync_settings': {
                'time_sync_enabled': True,
                'record_sync_enabled': True,
                'sync_timeout': 30
            },
            'gui_settings': {
                'show_copy_stats': True,
                'show_camera_preview': True,
                'dark_mode': False
            },
            'logging': {
                'level': 'INFO',
                'file_logging': True,
                'console_logging': True
            }
        }
        
        if not self.config_file.exists():
            logger.info(f"Creating new config file at {self.config_file}")
            save_json(default_config, self.config_file)
            return default_config
        
        config = load_json(self.config_file)
        if config is None:
            logger.warning("Failed to load config, using defaults")
            return default_config
        
        # Update the config with new fields from the default config
        updated = False
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
                updated = True
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if subkey not in config[key]:
                        config[key][subkey] = subvalue
                        updated = True
        
        if updated:
            save_json(config, self.config_file)
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the config"""
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """Set a value in the config"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        return save_json(self.config, self.config_file)
    
    def save(self) -> bool:
        """Save the config to a file"""
        return save_json(self.config, self.config_file)

# Create a global instance of the configuration
config = AppConfig()