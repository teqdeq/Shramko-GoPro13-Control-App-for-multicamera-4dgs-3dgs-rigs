# Copyright (c) 2024 Andrii Shramko
# Contact: zmei116@gmail.com
# LinkedIn: https://www.linkedin.com/in/andrii-shramko/
# Tags: #ShramkoVR #ShramkoCamera #ShramkoSoft
# License: This code is free to use for non-commercial projects.
# For commercial use, please contact Andrii Shramko at the above email or LinkedIn.

import requests
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from goprolist_and_start_usb import discover_gopro_devices
import logging
from threading import Barrier, Thread

def prepare_camera_for_sync(ip):
    """Подготовка камеры к синхронизации"""
    try:
        # Проверяем доступность камеры
        response = requests.get(f"http://{ip}:8080/gopro/camera/state", timeout=2)
        if response.status_code != 200:
            logging.error(f"Camera {ip} is not responding")
            return False
        return True
    except requests.RequestException as e:
        logging.error(f"Error preparing camera {ip}: {e}")
        return False

def sync_time_on_cameras():
    """Синхронизация времени на всех камерах с максимальной точностью"""
    devices = discover_gopro_devices()
    if not devices:
        logging.error("No GoPro devices found.")
        return

    camera_ips = [device["ip"] for device in devices]
    barrier = Barrier(len(camera_ips))

    def apply_time_sync(ip):
        try:
            # Подготовка данных времени
            current_time = datetime.now()
            date = current_time.strftime("%Y_%m_%d")
            time_str = current_time.strftime("%H_%M_%S")
            timezone_offset = int(current_time.utcoffset().total_seconds() / 60) if current_time.utcoffset() else 0
            dst = 1 if current_time.dst() else 0

            # Формируем URL и параметры
            url = f"http://{ip}:8080/gopro/camera/set_date_time"
            params = {
                "date": date,
                "time": time_str,
                "tzone": timezone_offset,
                "dst": dst
            }

            logging.info(f"Camera {ip} waiting at barrier for time sync")
            barrier.wait()  # Синхронизация всех потоков
            
            # Отправляем команду синхронизации времени
            start_time = time.time()
            response = requests.get(url, params=params, timeout=1)
            end_time = time.time()
            
            if response.status_code == 200:
                logging.info(f"Time set on camera {ip} at {start_time:.6f}, response at {end_time:.6f}")
                return True
            else:
                logging.error(f"Failed to set time on camera {ip}: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"Error setting time on camera {ip}: {e}")
            return False

    # Запускаем синхронизацию в отдельных потоках
    threads = []
    results = []
    for ip in camera_ips:
        thread = Thread(target=lambda: results.append((ip, apply_time_sync(ip))))
        threads.append(thread)
        thread.start()

    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()

    # Проверяем результаты
    if all(success for _, success in results):
        logging.info("Time synchronization completed successfully on all cameras")
    else:
        failed_cameras = [ip for ip, success in results if not success]
        logging.error(f"Time synchronization failed on cameras: {failed_cameras}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sync_time_on_cameras()
