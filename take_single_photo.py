import logging
import requests
import json
from pathlib import Path
import asyncio
import aiohttp
from utils import setup_logging, get_data_dir

# Create logger for this module
logger = setup_logging('take_single_photo')

def get_cached_devices():
    """Get list of cameras from cache"""
    try:
        cache_file = get_data_dir() / 'camera_cache.json'
        if not cache_file.exists():
            logger.error("Camera cache file not found")
            return []
            
        with open(cache_file, 'r') as f:
            return json.load(f)
            
    except Exception as e:
        logger.error(f"Error reading camera cache: {e}")
        return []

async def take_photo_async(session, camera_ip, camera_name):
    """Take a single photo on specified camera"""
    try:
        # Take photo with longer timeout
        shutter_url = f"http://{camera_ip}:8080/gp/gpControl/command/shutter?p=1"
        async with session.get(shutter_url, timeout=2.0) as response:
            if response.status == 200:
                logger.info(f"Photo taken successfully on camera {camera_name}")
                return True, None
            else:
                error_msg = f"Failed to take photo. Status code: {response.status}"
                logger.warning(f"Camera {camera_name}: {error_msg}")
                return False, error_msg
            
    except asyncio.TimeoutError:
        error_msg = "Timeout waiting for camera response (2000ms)"
        logger.warning(f"Camera {camera_name}: {error_msg}")
        return False, error_msg
    except aiohttp.ClientError as e:
        error_msg = f"Network error: {str(e)}"
        logger.warning(f"Camera {camera_name}: {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.warning(f"Camera {camera_name}: {error_msg}")
        return False, error_msg

async def take_photos_async(devices):
    """Take photos on all cameras simultaneously"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for device in devices:
            task = take_photo_async(session, device['ip'], device['name'])
            tasks.append(task)
        
        # Run all tasks simultaneously
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        # Analyze results
        failed_cameras = []
        for device, (success, error) in zip(devices, results):
            if not success:
                failed_cameras.append({
                    'name': device['name'],
                    'error': error
                })
        
        # If there are problematic cameras, log their details
        if failed_cameras:
            logger.warning("Problems detected with cameras:")
            for cam in failed_cameras:
                logger.warning(f"  - {cam['name']}: {cam['error']}")
        
        # Return True and the list of problematic cameras
        return True, failed_cameras

def main(devices=None):
    """Take photos on all connected cameras or specified devices"""
    try:
        # If no devices provided, get list from cache
        if devices is None:
            devices = get_cached_devices()
            
        if not devices:
            logger.error("No cameras found")
            return False, []
            
        # Take photos asynchronously
        success, failed_cameras = asyncio.run(take_photos_async(devices))
        return success, failed_cameras
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        return False, []

if __name__ == "__main__":
    main()