from zeroconf import Zeroconf, ServiceBrowser
import requests
import time
import logging
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Thread

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GoProListener:
    def __init__(self):
        self.devices = []

    def add_service(self, zeroconf, service_type, name):
        """Add a discovered GoPro device"""
        info = zeroconf.get_service_info(service_type, name)
        if info:
            ip_address = ".".join(map(str, info.addresses[0]))
            logging.info(f"Discovered GoPro: {name} at {ip_address}")
            self.devices.append({
                "name": name.split(".")[0],  # Store only the serial number
                "ip": ip_address
            })

    def remove_service(self, zeroconf, service_type, name):
        """Handle removal of a GoPro device"""
        logging.info(f"GoPro {name} removed")

# Discover GoPro devices
def discover_gopro_devices():
    """Discover GoPro devices on the network"""
    zeroconf = Zeroconf()
    listener = GoProListener()
    logging.info("Searching for GoPro cameras...")
    browser = ServiceBrowser(zeroconf, "_gopro-web._tcp.local.", listener)

    try:
        time.sleep(5)  # Allow time for discovery
    finally:
        zeroconf.close()

    return listener.devices

# Enable or reset USB control
def reset_and_enable_usb_control(camera_ip):
    """Reset and enable USB control on a camera"""
    logging.info(f"Resetting USB control on camera {camera_ip}.")
    toggle_usb_control(camera_ip, enable=False)
    time.sleep(2)
    toggle_usb_control(camera_ip, enable=True)

def toggle_usb_control(camera_ip, enable):
    """Toggle USB control on a camera"""
    action = 1 if enable else 0
    url = f"http://{camera_ip}:8080/gopro/camera/control/wired_usb?p={action}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            logging.info(f"USB control {'enabled' if enable else 'disabled'} on camera {camera_ip}.")
        else:
            logging.error(f"Failed to {'enable' if enable else 'disable'} USB control on camera {camera_ip}. "
                          f"Status Code: {response.status_code}. Response: {response.text}")
    except requests.RequestException as e:
        logging.error(f"Error toggling USB control on camera {camera_ip}: {e}")

# Start recording using barrier synchronization for simultaneous execution
def start_recording(camera_ip, barrier):
    """Start recording on a camera with barrier synchronization"""
    try:
        logging.info(f"Camera {camera_ip} waiting at the barrier.")
        barrier.wait()  # Wait for all threads to reach this point
        response = requests.get(f"http://{camera_ip}:8080/gopro/camera/shutter/start")
        if response.status_code == 200:
            logging.info(f"Recording started successfully on camera {camera_ip}.")
        else:
            logging.error(f"Failed to start recording on camera {camera_ip}. Status Code: {response.status_code}")
            logging.error(f"Response: {response.text}")
    except Exception as e:
        logging.error(f"An error occurred while starting recording on camera {camera_ip}: {e}")

# Synchronize time on all cameras
def sync_time_on_cameras():
    """Synchronize time on all cameras"""
    logging.info("Synchronizing time on all cameras...")
    # Placeholder for the function that syncs time on cameras

# Save discovered devices to cache
def save_devices_to_cache(devices, cache_file="camera_cache.json"):
    """Save discovered devices to a cache file"""
    try:
        with open(cache_file, "w") as file:
            json.dump(devices, file, indent=4)
        logging.info("Camera cache updated successfully.")
    except Exception as e:
        logging.error(f"Failed to save camera cache: {e}")

if __name__ == "__main__":
    # Step 1: Discover GoPro devices
    devices = discover_gopro_devices()
    if not devices:
        logging.info("No GoPro devices found.")
        exit()

    logging.info("Found the following GoPro devices:")
    for device in devices:
        logging.info(f"Name: {device['name']}, IP: {device['ip']}")

    # Save discovered devices to cache
    save_devices_to_cache(devices)

    # Step 2: Enable USB control on all cameras
    logging.info("Resetting and enabling USB control on all cameras...")
    with ThreadPoolExecutor() as executor:
        executor.map(lambda d: reset_and_enable_usb_control(d['ip']), devices)

    # Step 3: Synchronize time on all cameras
    logging.info("Synchronizing time on all cameras...")
    sync_time_on_cameras()
    time.sleep(1)  # Short pause after synchronization

    # Step 4: Start recording on all cameras simultaneously
    logging.info("Starting recording on all cameras...")

    # Create a barrier to synchronize all threads before starting recording
    barrier = Barrier(len(devices))

    threads = []
    for device in devices:
        thread = Thread(target=start_recording, args=(device['ip'], barrier))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
