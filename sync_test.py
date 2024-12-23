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
    try:
        response = requests.get(f"http://{camera_ip}:8080/gopro/camera/shutter/stop")
        if response.status_code == 200:
            logging.info(f"Recording stopped on camera {camera_ip}")
        else:
            logging.error(f"Failed to stop recording on {camera_ip}")
    except Exception as e:
        logging.error(f"Error stopping camera {camera_ip}: {e}")

def start_with_threadpool(devices, duration=3):
    logging.info("\n=== Starting ThreadPool test ===")
    
    def record_camera(camera_ip):
        start_time = time.time()
        try:
            response = requests.get(f"http://{camera_ip}:8080/gopro/camera/shutter/start")
            if response.status_code == 200:
                logging.info(f"Camera {camera_ip} started at {time.time():.6f}")
        except Exception as e:
            logging.error(f"Error starting camera {camera_ip}: {e}")
    
    # Запускаем запись
    with ThreadPoolExecutor() as executor:
        executor.map(record_camera, [d['ip'] for d in devices])
    
    # Ждем заданное время
    time.sleep(duration)
    
    # Останавливаем запись
    with ThreadPoolExecutor() as executor:
        executor.map(stop_recording, [d['ip'] for d in devices])
    
    logging.info("=== ThreadPool test completed ===\n")
    time.sleep(6)  # Увеличенная пауза между тестами

def start_with_barrier(devices, duration=4):
    logging.info("\n=== Starting Barrier test ===")
    barrier = Barrier(len(devices))
    
    def record_camera(camera_ip):
        try:
            logging.info(f"Camera {camera_ip} waiting at barrier")
            barrier.wait()
            start_time = time.time()
            
            response = requests.get(f"http://{camera_ip}:8080/gopro/camera/shutter/start")
            if response.status_code == 200:
                logging.info(f"Camera {camera_ip} started at {time.time():.6f}")
        except Exception as e:
            logging.error(f"Error starting camera {camera_ip}: {e}")
    
    # Запускаем потоки для записи
    threads = []
    for device in devices:
        thread = Thread(target=record_camera, args=(device['ip'],))
        threads.append(thread)
        thread.start()
    
    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()
    
    # Ждем заданное время
    time.sleep(duration)
    
    # Останавливаем запись
    with ThreadPoolExecutor() as executor:
        executor.map(stop_recording, [d['ip'] for d in devices])
    
    logging.info("=== Barrier test completed ===\n")
    time.sleep(6)  # Увеличенная пауза между тестами

def run_sync_tests():
    devices = discover_gopro_devices()
    if not devices:
        logging.error("No cameras found")
        return
    
    logging.info(f"Found {len(devices)} cameras")
    
    # Три теста с ThreadPool (по 3 секунды)
    for i in range(3):
        logging.info(f"\nThreadPool Test #{i+1}")
        start_with_threadpool(devices, duration=3)
    
    time.sleep(5)  # Пауза между сериями тестов
    
    # Три теста с Barrier (по 4 секунды)
    for i in range(3):
        logging.info(f"\nBarrier Test #{i+1}")
        start_with_barrier(devices, duration=4)

if __name__ == "__main__":
    run_sync_tests() 