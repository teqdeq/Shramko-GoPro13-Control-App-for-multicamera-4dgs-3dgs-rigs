import asyncio
import aiohttp
import logging
import json
from datetime import datetime
from goprolist_and_start_usb import discover_gopro_devices

# Setting up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Creating a list of all IDs from 1 to 200
SETTINGS_TO_CHECK = [{"id": i, "name": f"Setting ID {i}"} for i in range(1, 201)]

# Dictionary to store results only with available values
valid_settings_data = {}

async def check_setting_values(session, camera_ip, setting):
    """Checking available values for the setting"""
    try:
        # Trying to set an incorrect value to get a list of available ones
        url = f"http://{camera_ip}:8080/gopro/camera/setting?setting={setting['id']}&option=999999"
        async with session.get(url, timeout=5) as response:
            if response.status == 403:
                error_data = await response.json()
                has_valid_data = False
                setting_data = {
                    "id": setting['id'],
                    "status_code": response.status
                }

                if 'supported_options' in error_data:
                    supported_options = error_data['supported_options']
                    if supported_options: # Checking that the list is not empty
                        has_valid_data = True
                        setting_data["supported_options"] = supported_options
                        logging.info(f"\nAvailable values for Setting ID {setting['id']}:")
                        # Available values for Setting ID {setting['id']}:
                        for option in supported_options:
                            logging.info(f"  {option['display_name']} (ID: {option['id']})")

                elif 'available_options' in error_data:
                    available_options = error_data['available_options']
                    if available_options: # Checking that the list is not empty
                        has_valid_data = True
                        setting_data["available_options"] = available_options
                        logging.info(f"  Available options: {available_options}")

                # Saving only if there are available values
                if has_valid_data:
                    valid_settings_data[setting['id']] = setting_data
                    
            elif response.status == 200:
                try:
                    current_value = await response.json()
                    if current_value is not None: # Checking that the value is not None
                        setting_data = {
                            "id": setting['id'],
                            "status_code": response.status,
                            "current_value": current_value
                        }
                        valid_settings_data[setting['id']] = setting_data
                        logging.info(f"\nCurrent value for Setting ID {setting['id']}: {current_value}")
                        # Current value for Setting ID {setting['id']}: {current_value}
                except:
                    pass # Skipping if it was not possible to parse the response
            
    except Exception as e:
        logging.error(f"Error checking setting ID {setting['id']}: {e}")

def save_settings_to_file(settings_data, camera_ip):
    """Saving settings to file"""
    try:
        # Creating a data structure with metadata
        output_data = {
            "metadata": {
                "camera_ip": camera_ip,
                "scan_date": datetime.now().isoformat(),
                "total_valid_settings": len(settings_data)
            },
            "settings": settings_data
        }
        
        # Saving to file
        with open('all_avalable_gopro10_value_settings.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        logging.info(f"\nFound {len(settings_data)} settings with available values")
        logging.info("Results saved to file: all_avalable_gopro10_value_settings.json")
        
    except Exception as e:
        logging.error(f"Error saving settings to file: {e}")

async def main_async(devices):
    """Main asynchronous function"""
    try:
        if not devices:
            logging.error("No cameras found")
            return
            
        async with aiohttp.ClientSession() as session:
            for device in devices:
                camera_ip = device['ip']
                logging.info(f"\nChecking settings for camera {camera_ip}")
                
                # Clearing the dictionary before a new scan
                valid_settings_data.clear()
                
                for setting in SETTINGS_TO_CHECK:
                    await check_setting_values(session, camera_ip, setting)
                    await asyncio.sleep(0.3)  # Pause between requests
                
                # Saving only settings with available values
                save_settings_to_file(valid_settings_data, camera_ip)
            
    except Exception as e:
        logging.error(f"Error in main: {e}")

def main():
    """Entry point"""
    try:
        logging.info("Starting settings check")
        
        # Searching for cameras
        devices = discover_gopro_devices()
        
        if not devices:
            logging.error("No cameras found")
            return
            
        # Starting the check
        asyncio.run(main_async(devices))
        
    except KeyboardInterrupt:
        logging.info("Check stopped by user")
    except Exception as e:
        logging.error(f"Error in main: {e}", exc_info=True)

if __name__ == "__main__":
    main()