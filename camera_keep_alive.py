import requests
import logging
from typing import Optional

class CameraKeepAlive:
    """Manages keep-alive functionality for GoPro cameras"""
    
    def __init__(self, camera_ip: str):
        self.camera_ip = camera_ip
        self.base_url = f"http://{camera_ip}:8080"
        self.logger = logging.getLogger(__name__)
        
    def keep_alive(self) -> bool:
        """Send keep-alive command to prevent screen timeout"""
        try:
            # Send keep-alive command as per OpenAPI spec
            response = requests.get(f"{self.base_url}/gp/gpControl/command/keep_alive", timeout=2)
            if response.status_code != 200:
                self.logger.error(f"Keep-alive failed: {response.status_code}")
                return False
                
            # Send screen wake command to prevent screen timeout
            response = requests.get(f"{self.base_url}/gp/gpControl/command/screen_wake", timeout=2)
            if response.status_code != 200:
                self.logger.error(f"Screen wake failed: {response.status_code}")
                return False
                
            # Send status command to maintain connection
            response = requests.get(f"{self.base_url}/gp/gpControl/status", timeout=2)
            if response.status_code != 200:
                self.logger.error(f"Status check failed: {response.status_code}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending keep-alive: {str(e)}")
            return False
            
    def get_status(self) -> Optional[dict]:
        """Get camera status"""
        try:
            response = requests.get(f"{self.base_url}/gp/gpControl/status", timeout=2)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            self.logger.error(f"Error getting camera status: {str(e)}")
            return None 