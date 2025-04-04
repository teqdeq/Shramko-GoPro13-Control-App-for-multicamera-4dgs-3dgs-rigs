import time
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Thread
import requests
from goprolist_and_start_usb import discover_gopro_devices

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d - %(message)s',
    datefmt='%H:%M:%S'
)

def stop_recording(camera_ip):
    """Stop recording on a specific camera"""
    try:
        response = requests.get(f"http://{camera_ip}:8080/gopro/camera/shutter/stop")
        if response.status_code == 200:
            logging.info(f"Recording stopped on camera {camera_ip}")
        else:
            logging.error(f"Failed to stop recording on {camera_ip}")
    except Exception as e:
        logging.error(f"Error stopping camera {camera_ip}: {e}")

def start_with_threadpool(devices, duration=3):
    """Start recording using ThreadPoolExecutor"""
    logging.info("\n=== Starting ThreadPool test ===")
    
    def record_camera(camera_ip):
        """Start recording on a specific camera"""
        start_time = time.time()
        try:
            response = requests.get(f"http://{camera_ip}:8080/gopro/camera/shutter/start")
            if response.status_code == 200:
                logging.info(f"Camera {camera_ip} started at {time.time():.6f}")
        except Exception as e:
            logging.error(f"Error starting camera {camera_ip}: {e}")
    
    # Start recording
    with ThreadPoolExecutor() as executor:
        executor.map(record_camera, [d['ip'] for d in devices])
    
    # Wait for the specified duration
    time.sleep(duration)
    
    # Stop recording
    with ThreadPoolExecutor() as executor:
        executor.map(stop_recording, [d['ip'] for d in devices])
    
    logging.info("=== ThreadPool test completed ===\n")
    time.sleep(6)  # Increased pause between tests

def start_with_barrier(devices, duration=4):
    """Start recording using Barrier synchronization"""
    logging.info("\n=== Starting Barrier test ===")
    barrier = Barrier(len(devices))
    
    def record_camera(camera_ip):
        """Start recording on a specific camera with barrier synchronization"""
        try:
            logging.info(f"Camera {camera_ip} waiting at barrier")
            barrier.wait()
            start_time = time.time()
            
            response = requests.get(f"http://{camera_ip}:8080/gopro/camera/shutter/start")
            if response.status_code == 200:
                logging.info(f"Camera {camera_ip} started at {time.time():.6f}")
        except Exception as e:
            logging.error(f"Error starting camera {camera_ip}: {e}")
    
    # Start threads for recording
    threads = []
    for device in devices:
        thread = Thread(target=record_camera, args=(device['ip'],))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to finish
    for thread in threads:
        thread.join()
    
    # Wait for the specified duration
    time.sleep(duration)
    
    # Stop recording
    with ThreadPoolExecutor() as executor:
        executor.map(stop_recording, [d['ip'] for d in devices])
    
    logging.info("=== Barrier test completed ===\n")
    time.sleep(6)  # Increased pause between tests

def run_sync_tests():
    """Run synchronization tests on discovered cameras"""
    devices = discover_gopro_devices()
    if not devices:
        logging.error("No cameras found")
        return
    
    logging.info(f"Found {len(devices)} cameras")
    
    # Three tests with ThreadPool (3 seconds each)
    for i in range(3):
        logging.info(f"\nThreadPool Test #{i+1}")
        start_with_threadpool(devices, duration=3)
    
    time.sleep(5)  # Pause between test series
    
    # Three tests with Barrier (4 seconds each)
    for i in range(3):
        logging.info(f"\nBarrier Test #{i+1}")
        start_with_barrier(devices, duration=4)

if __name__ == "__main__":
    run_sync_tests()