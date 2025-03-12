import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class PreviewConfig:
    enabled: bool = False
    quality: int = 50
    auto_refresh: bool = True

@dataclass
class GridConfig:
    card_width: int = 300
    card_height: int = 400
    spacing: int = 10

@dataclass
class MonitorConfig:
    update_interval: int = 1000  # ms
    preview: PreviewConfig = PreviewConfig()
    grid: GridConfig = GridConfig()
    window_width: int = 800
    window_height: int = 600
    
class Config:
    """Configuration manager"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        
    def _load_config(self) -> MonitorConfig:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return MonitorConfig(**data)
        except Exception as e:
            print(f"Error loading config: {str(e)}")
            
        return MonitorConfig()
        
    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.config), f, indent=4)
        except Exception as e:
            print(f"Error saving config: {str(e)}")
            
    def get_preview_config(self) -> PreviewConfig:
        """Get preview configuration"""
        return self.config.preview
        
    def get_grid_config(self) -> GridConfig:
        """Get grid configuration"""
        return self.config.grid
        
    def update_preview_config(self, enabled: Optional[bool] = None,
                            quality: Optional[int] = None,
                            auto_refresh: Optional[bool] = None):
        """Update preview configuration"""
        if enabled is not None:
            self.config.preview.enabled = enabled
        if quality is not None:
            self.config.preview.quality = quality
        if auto_refresh is not None:
            self.config.preview.auto_refresh = auto_refresh
        self.save()
        
    def update_grid_config(self, card_width: Optional[int] = None,
                          card_height: Optional[int] = None,
                          spacing: Optional[int] = None):
        """Update grid configuration"""
        if card_width is not None:
            self.config.grid.card_width = card_width
        if card_height is not None:
            self.config.grid.card_height = card_height
        if spacing is not None:
            self.config.grid.spacing = spacing
        self.save()
        
    def update_window_size(self, width: int, height: int):
        """Update window size configuration"""
        self.config.window_width = width
        self.config.window_height = height
        self.save()
        
    def get_window_size(self) -> tuple[int, int]:
        """Get configured window size"""
        return (self.config.window_width, self.config.window_height)
        
    def get_update_interval(self) -> int:
        """Get status update interval"""
        return self.config.update_interval
        
    def set_update_interval(self, interval: int):
        """Set status update interval"""
        self.config.update_interval = interval
        self.save() 