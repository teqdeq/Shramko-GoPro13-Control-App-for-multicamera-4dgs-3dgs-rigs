import logging
import requests
from dataclasses import dataclass
from typing import Dict, Optional
import sys
import os

# Add root directory path for importing existing modules
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

@dataclass
class CameraState:
    """Camera state"""
    system_busy: bool = False  # Busy (8) - set while loading presets, changing settings, formatting sdcard
    encoding_active: bool = False  # Encoding (10) - set while capturing photo/video media
    camera_control: int = 0  # Camera Control ID (114) - 0:IDLE, 1:CAMERA, 2:EXTERNAL, 3:SETUP
    battery_level: int = 0  # Internal Battery Percentage (70)
    storage_remaining: float = 0  # SD Card Remaining (54) in bytes
    storage_total: float = 0  # SD Card Capacity (117) in bytes
    remaining_photos: int = 0  # Remaining Photos (34)
    remaining_video_time: int = 0  # Remaining Video Time (35) in seconds
    is_cold: bool = False  # Cold status (85)
    
    @property
    def storage_remaining_gb(self) -> float:
        """Convert remaining storage to GB"""
        return self.storage_remaining / (1024 * 1024 * 1024)
    
    @property
    def storage_total_gb(self) -> float:
        """Convert total storage to GB"""
        return self.storage_total / (1024 * 1024 * 1024)
    
    @property
    def storage_used_gb(self) -> float:
        """Calculate used storage in GB"""
        return self.storage_total_gb - self.storage_remaining_gb
    
    @property
    def storage_percent_used(self) -> int:
        """Calculate percentage of storage used"""
        if self.storage_total == 0:
            return 0
        return int((self.storage_used_gb / self.storage_total_gb) * 100)

class CameraStatusManager:
    """Manages GoPro HERO13 camera state"""
    
    def __init__(self, camera_ip: str):
        self.logger = logging.getLogger(__name__)
        self.camera_ip = camera_ip
        self.base_url = f"http://{camera_ip}:8080"
        self.state = CameraState()
        
    def update_state(self) -> bool:
        """Updates camera state"""
        try:
            # Get camera status
            response = requests.get(f"{self.base_url}/gopro/camera/state", timeout=2)
            self.logger.debug(f"Camera state response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                status_data = data.get("status", {})
                
                # Get system busy and encoding status according to API documentation
                old_busy = self.state.system_busy
                self.state.system_busy = bool(int(status_data.get("8", "0")))  # Busy (8)
                if old_busy != self.state.system_busy:
                    self.logger.info(f"System busy changed: {old_busy} -> {self.state.system_busy}")
                
                old_encoding = self.state.encoding_active
                self.state.encoding_active = bool(int(status_data.get("10", "0")))  # Encoding (10)
                if old_encoding != self.state.encoding_active:
                    self.logger.info(f"Encoding active changed: {old_encoding} -> {self.state.encoding_active}")
                
                # Get camera control status (114)
                old_control = self.state.camera_control
                self.state.camera_control = int(status_data.get("114", "0"))
                if old_control != self.state.camera_control:
                    self.logger.info(f"Camera control changed: {old_control} -> {self.state.camera_control}")
                
                # Get temperature status (85)
                old_cold = self.state.is_cold
                self.state.is_cold = bool(int(status_data.get("85", "0")))
                if old_cold != self.state.is_cold:
                    self.logger.info(f"Cold status changed: {old_cold} -> {self.state.is_cold}")
                
                # Get battery level (70)
                old_battery = self.state.battery_level
                self.state.battery_level = int(status_data.get("70", "0"))
                if old_battery != self.state.battery_level:
                    self.logger.info(f"Battery level changed: {old_battery} -> {self.state.battery_level}")
                
                # Get storage info
                old_photos = self.state.remaining_photos
                self.state.remaining_photos = int(status_data.get("34", "0"))
                if old_photos != self.state.remaining_photos:
                    self.logger.info(f"Remaining photos changed: {old_photos} -> {self.state.remaining_photos}")
                
                old_video_time = self.state.remaining_video_time
                self.state.remaining_video_time = int(status_data.get("35", "0"))
                if old_video_time != self.state.remaining_video_time:
                    self.logger.info(f"Remaining video time changed: {old_video_time} -> {self.state.remaining_video_time}")
                
                # Get storage info - values are in MB from API
                old_storage = self.state.storage_remaining
                self.state.storage_remaining = float(status_data.get("54", "0")) * 1024 * 1024  # Convert MB to bytes
                if old_storage != self.state.storage_remaining:
                    self.logger.info(f"Storage remaining changed: {old_storage/1024/1024/1024:.2f}GB -> {self.state.storage_remaining_gb:.2f}GB")
                
                old_total = self.state.storage_total
                self.state.storage_total = float(status_data.get("117", "0")) * 1024 * 1024  # Convert MB to bytes
                if old_total != self.state.storage_total:
                    self.logger.info(f"Storage total changed: {old_total/1024/1024/1024:.2f}GB -> {self.state.storage_total_gb:.2f}GB")
                
                # Log final state
                self.logger.info("Camera state summary:")
                self.logger.info(f"System busy: {self.state.system_busy}, Encoding: {self.state.encoding_active}, Control: {self.state.camera_control}, Cold: {self.state.is_cold}")
                self.logger.info(f"Battery: {self.state.battery_level}%, Storage: {self.state.storage_remaining_gb:.2f}GB/{self.state.storage_total_gb:.2f}GB ({self.state.storage_percent_used}% used)")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating camera state: {str(e)}")
            return False
            
    def get_state_dict(self) -> Dict:
        """Returns state as dictionary"""
        return {
            "system_busy": self.state.system_busy,
            "encoding_active": self.state.encoding_active,
            "camera_control": self.state.camera_control,
            "battery_level": self.state.battery_level,
            "storage_remaining": self.state.storage_remaining,
            "storage_total": self.state.storage_total,
            "remaining_photos": self.state.remaining_photos,
            "remaining_video_time": self.state.remaining_video_time,
            "is_cold": self.state.is_cold
        }
        
    def start_preview(self) -> bool:
        """Starts camera preview"""
        try:
            # Check if system is busy or encoding
            if self.state.system_busy or self.state.encoding_active:
                self.logger.warning(f"Cannot start preview - System busy: {self.state.system_busy}, Encoding: {self.state.encoding_active}")
                return False
                
            # Start preview stream
            response = requests.get(f"{self.base_url}/gopro/camera/stream/start", timeout=2)
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Error starting preview: {str(e)}")
            return False
            
    def stop_preview(self) -> bool:
        """Stops camera preview"""
        try:
            # Stop preview stream
            response = requests.get(f"{self.base_url}/gopro/camera/stream/stop", timeout=2)
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Error stopping preview: {str(e)}")
            return False 