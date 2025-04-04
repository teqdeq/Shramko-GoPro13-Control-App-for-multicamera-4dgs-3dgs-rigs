import requests
import logging
import time
from goprolist_and_start_usb import discover_gopro_devices

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_setting(camera_ip, setting_id, value):
    """Test a specific camera setting"""
    try:
        url = f"http://{camera_ip}:8080/gp/gpControl/setting/{setting_id}/{value}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            logging.info(f"Successfully applied setting {setting_id}: {value}")
            return True
        else:
            logging.warning(f"Failed to apply setting {setting_id}: {value} (Status: {response.status_code})")
            return False
    except Exception as e:
        logging.error(f"Error applying setting {setting_id}: {e}")
        return False

def main():
    try:
        # Discover cameras
        logging.info("Discovering cameras...")
        devices = discover_gopro_devices()
        
        if not devices:
            logging.error("No cameras found")
            return
            
        # Use the first camera
        camera = devices[0]
        camera_ip = camera['ip']
        logging.info(f"\nTesting settings on camera: {camera['name']}")
        
        # Test Photo Output (125)
        setting_id = 125
        logging.info(f"\nTesting Photo Output (ID: {setting_id})")
        
        # Test value 0 (Standard)
        logging.info(f"Testing value 0 (Standard)...")
        test_setting(camera_ip, setting_id, 0)
        time.sleep(3)  # Wait for 3 seconds
        
        # Test value 1 (RAW)
        logging.info(f"Testing value 1 (RAW)...")
        test_setting(camera_ip, setting_id, 1)
        time.sleep(3)  # Wait for 3 seconds
        
        logging.info("\nTesting completed!")
        
    except Exception as e:
        logging.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()