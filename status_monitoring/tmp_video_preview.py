import socket
import requests
import time
import logging
import sys
import os
import subprocess
from zeroconf import ServiceBrowser, Zeroconf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('preview_stream.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def discover_gopro_devices():
    cameras = []
    class MyListener:
        def add_service(self, zc, type_, name):
            info = zc.get_service_info(type_, name)
            if info:
                camera = {
                    'name': name,
                    'ip': socket.inet_ntoa(info.addresses[0]),
                    'port': info.port
                }
                cameras.append(camera)
        
        def update_service(self, zc, type_, name):
            pass

    zeroconf = Zeroconf()
    browser = ServiceBrowser(zeroconf, "_gopro-web._tcp.local.", MyListener())
    time.sleep(5)
    zeroconf.close()
    return cameras

def start_preview(camera_ip):
    """Start preview stream from GoPro camera"""
    try:
        # Start preview stream on port 8556 as per documentation
        response = requests.get(f"http://{camera_ip}:8080/gopro/camera/stream/start?port=8556")
        if response.status_code != 200:
            logging.error(f"Failed to start preview stream: {response.status_code}")
            return False
        logging.info("Successfully started preview stream")
        return True
    except Exception as e:
        logging.error(f"Error starting preview stream: {e}")
        return False

def stop_preview(camera_ip):
    """Stop preview stream"""
    try:
        response = requests.get(f"http://{camera_ip}:8080/gopro/camera/stream/stop")
        if response.status_code != 200:
            logging.error(f"Failed to stop preview stream")
            return False
        logging.info("Successfully stopped preview stream")
        return True
    except Exception as e:
        logging.error(f"Error stopping preview stream: {e}")
        return False

def main():
    # Discover GoPro cameras
    logging.info("Searching for GoPro cameras...")
    cameras = discover_gopro_devices()
    
    if not cameras:
        logging.error("No GoPro cameras found")
        return
        
    # Use first camera found
    camera = cameras[0]
    camera_ip = camera['ip']
    logging.info(f"Using camera at {camera_ip}")

    # Start preview stream
    if not start_preview(camera_ip):
        return

    try:
        # Start VLC to view the stream
        vlc_cmd = [
            "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
            "udp://@:8554",
            "--network-caching=50",  # Minimal caching for live preview
            "--udp-timeout=1000",
            "--no-audio"
        ]
        
        logging.info(f"Starting VLC with command: {' '.join(vlc_cmd)}")
        vlc_process = subprocess.Popen(vlc_cmd)
        
        # Keep script running until user interrupts
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        logging.info("Stopping preview stream...")
    finally:
        stop_preview(camera_ip)
        if 'vlc_process' in locals():
            vlc_process.terminate()

if __name__ == "__main__":
    main()