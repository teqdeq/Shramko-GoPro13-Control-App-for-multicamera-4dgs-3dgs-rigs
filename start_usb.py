import requests
import logging
import time
import sys
import os

# Настройка корневого логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Создаем логгер для этого модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def reset_usb_control(camera_ip):
    """Reset USB control for a specific camera"""
    try:
        print(f"DEBUG: Resetting USB for {camera_ip}")
        logger.error(f"Resetting USB control for camera {camera_ip}")
        
        url = f"http://{camera_ip}:8080/gopro/camera/control/wired_usb?p=0"
        print(f"DEBUG: Sending disable USB request to {url}")
        
        # Пробуем несколько раз с увеличивающимся таймаутом
        timeouts = [0.5, 1.0, 2.0]
        for timeout in timeouts:
            try:
                print(f"DEBUG: Trying with timeout {timeout}s")
                response = requests.get(url, timeout=timeout)
                print(f"DEBUG: Got response: {response.status_code}")
                
                if response.status_code == 200 or response.status_code == 500:  # 500 означает что USB уже отключен
                    print(f"DEBUG: USB disable successful (status: {response.status_code})")
                    time.sleep(0.5)  # Небольшая пауза для стабилизации
                    return True
                else:
                    print(f"DEBUG: USB disable failed with unexpected status {response.status_code}")
                    try:
                        print(f"DEBUG: Response content: {response.text}")
                    except:
                        print("DEBUG: Could not get response content")
                    
            except requests.exceptions.Timeout:
                print(f"DEBUG: Request timed out after {timeout}s")
                continue
            except requests.exceptions.ConnectionError as e:
                print(f"DEBUG: Connection error: {str(e)}")
                continue
            except Exception as e:
                print(f"DEBUG: Request error: {str(e)}")
                continue
                
        logger.error(f"Failed to reset USB control for camera {camera_ip} after all retries")
        return False
            
    except Exception as e:
        print(f"DEBUG: Outer error: {str(e)}")
        logger.error(f"Error resetting USB control for camera {camera_ip}: {str(e)}")
        return False

def enable_usb_control(camera_ip):
    """Enable USB control for a specific camera"""
    try:
        print(f"DEBUG: Enabling USB for {camera_ip}")
        logger.error(f"Enabling USB control for camera {camera_ip}")
        
        url = f"http://{camera_ip}:8080/gopro/camera/control/wired_usb?p=1"
        print(f"DEBUG: Sending enable USB request to {url}")
        
        # Пробуем несколько раз с увеличивающимся таймаутом
        timeouts = [0.5, 1.0, 2.0]
        for timeout in timeouts:
            try:
                print(f"DEBUG: Trying with timeout {timeout}s")
                response = requests.get(url, timeout=timeout)
                print(f"DEBUG: Got response: {response.status_code}")
                
                if response.status_code == 200 or response.status_code == 500:  # 500 может означать что USB уже включен
                    print(f"DEBUG: USB enable successful (status: {response.status_code})")
                    time.sleep(0.5)  # Пауза для стабилизации
                    return True
                else:
                    print(f"DEBUG: USB enable failed with unexpected status {response.status_code}")
                    try:
                        print(f"DEBUG: Response content: {response.text}")
                    except:
                        print("DEBUG: Could not get response content")
                    
            except requests.exceptions.Timeout:
                print(f"DEBUG: Request timed out after {timeout}s")
                continue
            except requests.exceptions.ConnectionError as e:
                print(f"DEBUG: Connection error: {str(e)}")
                continue
            except Exception as e:
                print(f"DEBUG: Request error: {str(e)}")
                continue
                
        logger.error(f"Failed to enable USB control for camera {camera_ip} after all retries")
        return False
            
    except Exception as e:
        print(f"DEBUG: Outer error: {str(e)}")
        logger.error(f"Error enabling USB control for camera {camera_ip}: {str(e)}")
        return False

def verify_usb_control(camera_ip):
    """Verify USB control is enabled for a specific camera"""
    try:
        print(f"DEBUG: Verifying USB for {camera_ip}")
        logger.error(f"Verifying USB control for camera {camera_ip}")
        
        url = f"http://{camera_ip}:8080/gopro/camera/state"
        print(f"DEBUG: Sending state request to {url}")
        
        # Пробуем несколько раз
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=1.0)
                print(f"DEBUG: Got response: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        state = response.json()
                        usb_status = state.get('status', {}).get('33', None)
                        print(f"DEBUG: USB status: {usb_status}")
                        logger.error(f"Camera {camera_ip} USB status: {usb_status}")
                        if usb_status == 1:
                            return True
                        # Если статус 0 или None, продолжаем попытки
                    except Exception as e:
                        print(f"DEBUG: Error parsing state: {str(e)}")
                        continue
                else:
                    print(f"DEBUG: State request failed with status {response.status_code}")
                    continue
                    
            except Exception as e:
                print(f"DEBUG: Attempt {attempt + 1} failed: {str(e)}")
                continue
                
        logger.error(f"Failed to verify USB control for camera {camera_ip} after all attempts")
        return False
            
    except Exception as e:
        print(f"DEBUG: Outer error: {str(e)}")
        logger.error(f"Error verifying USB control: {str(e)}")
        return False

def main(camera_ip):
    """Main function to reset and enable USB control for a specific camera"""
    try:
        print(f"\nDEBUG: === Starting USB control for {camera_ip} ===")
        print(f"DEBUG: Python version: {sys.version}")
        print(f"DEBUG: Current working directory: {os.getcwd()}")
        
        logger.error(f"=== Starting USB control sequence for camera {camera_ip} ===")
        
        # Reset USB control
        if not reset_usb_control(camera_ip):
            logger.error("Failed to reset USB control")
            return False
        
        # Небольшая пауза между командами
        print("DEBUG: Waiting 1s between disable and enable")
        time.sleep(1.0)
        
        # Enable USB control
        if not enable_usb_control(camera_ip):
            logger.error("Failed to enable USB control")
            return False
        
        # Пауза для стабилизации
        print("DEBUG: Waiting 0.5s for USB to stabilize")
        time.sleep(0.5)
        
        # Verify USB control
        usb_ok = verify_usb_control(camera_ip)
        if not usb_ok:
            logger.error("USB control may not be verified but commands were successful")
        
        # Проверяем текущий режим камеры
        print("DEBUG: Checking current camera mode")
        try:
            response = requests.get(f"http://{camera_ip}:8080/gopro/camera/state", timeout=1.0)
            if response.status_code == 200:
                state = response.json()
                current_mode = state.get('status', {}).get('43', None)
                if current_mode == 1:  # 1 = Photo Mode
                    print("DEBUG: Camera already in photo mode")
                    logger.info("Camera already in photo mode")
                    return True
        except Exception as e:
            print(f"DEBUG: Error checking camera mode: {str(e)}")
            # Продолжаем попытку установить режим
        
        # Устанавливаем режим фото только если не смогли определить текущий режим
        print("DEBUG: Setting photo mode")
        import photo_mode
        import asyncio
        import aiohttp
        
        try:
            # Даем камере время на инициализацию после USB
            time.sleep(1.0)
            
            # Создаем фейковое устройство для одной камеры
            device = {'ip': camera_ip, 'name': f"Camera_{camera_ip}"}
            
            # Пробуем установить фото режим несколько раз
            for attempt in range(3):
                print(f"DEBUG: Setting photo mode attempt {attempt + 1}")
                
                # Запускаем асинхронную установку режима
                async def set_photo():
                    async with aiohttp.ClientSession() as session:
                        return await photo_mode.set_photo_mode_async(session, device['ip'], device['name'])
                
                if asyncio.run(set_photo()):
                    logger.error("Photo mode set successfully")
                    return True
                    
                print(f"DEBUG: Failed to set photo mode, waiting before retry")
                time.sleep(1.0)
                
            logger.error("Failed to set photo mode after all attempts")
            return False
            
        except Exception as e:
            print(f"DEBUG: Error setting photo mode: {str(e)}")
            logger.error(f"Error setting photo mode: {str(e)}")
            return False
        
    except Exception as e:
        print(f"DEBUG: Error in main: {str(e)}")
        logger.error(f"Error in USB control sequence for camera {camera_ip}: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python start_usb.py <camera_ip>")
        sys.exit(1)
    
    success = main(sys.argv[1])
    sys.exit(0 if success else 1) 