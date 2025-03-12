import requests
import logging
import time
from typing import Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CameraStatusTester:
    def __init__(self, camera_ip: str):
        self.camera_ip = camera_ip
        self.base_url = f"http://{camera_ip}:8080"
        self.logger = logging.getLogger(__name__)
        
    def get_camera_state(self) -> Optional[Dict]:
        """Get camera state from API"""
        try:
            response = requests.get(f"{self.base_url}/gopro/camera/state", timeout=2)
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", {})
                
                # Get documented status flags
                system_busy = bool(int(status.get("8", "0")))  # Busy (8)
                encoding_active = bool(int(status.get("10", "0")))  # Encoding (10)
                camera_control = int(status.get("114", "0"))  # Camera Control ID (114)
                battery = int(status.get("70", "0"))  # Internal Battery Percentage (70)
                
                self.logger.info(f"\nCamera Status Summary:")
                self.logger.info(f"System Busy: {system_busy} (status 8)")
                self.logger.info(f"Encoding Active: {encoding_active} (status 10)")
                self.logger.info(f"Camera Control: {camera_control} (0=IDLE, 1=CAMERA, 2=EXTERNAL, 3=SETUP)")
                self.logger.info(f"Battery Level: {battery}%")
                
                return {
                    "system_busy": system_busy,
                    "encoding_active": encoding_active,
                    "camera_control": camera_control,
                    "battery": battery
                }
            else:
                self.logger.error(f"Failed to get camera state. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting camera state: {str(e)}")
            return None
            
    def set_camera_control(self, mode: int) -> bool:
        """Set camera control mode
        mode: 0=IDLE, 1=CAMERA, 2=EXTERNAL, 3=SETUP
        Returns True if successful
        """
        try:
            # Check camera state
            state = self.get_camera_state()
            if not state:
                return False
                
            # According to API docs, wait for both System Busy and Encoding Active flags
            if state["system_busy"] or state["encoding_active"]:
                self.logger.error("Camera busy or encoding - cannot send commands")
                return False

            response = requests.get(f"{self.base_url}/gopro/camera/control/set_ui_controller?p={mode}", timeout=2)
            success = response.status_code == 200
            if success:
                self.logger.info(f"Successfully set camera control to mode {mode}")
            else:
                self.logger.error(f"Failed to set camera control. Status code: {response.status_code}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error setting camera control: {str(e)}")
            return False
            
    def test_camera_status(self):
        """Test camera status and control"""
        self.logger.info("\n=== Starting Camera Status Test ===")
        
        # 1. Get initial state
        self.logger.info("\n1. Getting initial camera state...")
        initial_state = self.get_camera_state()
        if not initial_state:
            self.logger.error("Failed to get initial state")
            return
            
        # 2. Try to take control
        self.logger.info("\n2. Attempting to take external control...")
        if self.set_camera_control(2):  # EXTERNAL control
            time.sleep(1)  # Wait for status update
            control_state = self.get_camera_state()
            if control_state and control_state["camera_control"] == 2:
                self.logger.info("Successfully took external control")
            else:
                self.logger.error("Failed to verify external control")
                
        # 3. Release control
        self.logger.info("\n3. Releasing control (setting to IDLE)...")
        if self.set_camera_control(0):  # IDLE
            time.sleep(1)  # Wait for status update
            final_state = self.get_camera_state()
            if final_state and final_state["camera_control"] == 0:
                self.logger.info("Successfully released control")
            else:
                self.logger.error("Failed to verify control release")
                
        self.logger.info("\n=== Camera Status Test Complete ===")

def main():
    # Test with first camera
    try:
        # Import existing camera discovery
        import sys
        import os
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(root_dir)
        from goprolist_and_start_usb import discover_gopro_devices
        
        cameras = discover_gopro_devices()
        if not cameras:
            logging.error("No cameras found")
            return
            
        # Test first camera
        camera = cameras[0]
        tester = CameraStatusTester(camera['ip'])
        tester.test_camera_status()
        
    except Exception as e:
        logging.error(f"Test failed: {str(e)}")

if __name__ == "__main__":
    main() 