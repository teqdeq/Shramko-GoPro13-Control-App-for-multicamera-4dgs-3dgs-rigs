# Copyright (c) 2024 Andrii Shramko
# This code includes portions of GoPro API code licensed under MIT License.
# Copyright (c) 2017 Konrad Iturbe
# 
# Contact: zmei116@gmail.com
# LinkedIn: https://www.linkedin.com/in/andrii-shramko/
# Tags: #ShramkoVR #ShramkoCamera #ShramkoSoft
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import requests
import logging
import time
import asyncio
import aiohttp
from utils import setup_logging, check_dependencies
from goprolist_and_start_usb import discover_gopro_devices

# Initialize logging with the module name
logger = setup_logging(__name__)

async def set_timelapse_mode_async(session, camera_ip, camera_name):
    """Asynchronously set timelapse mode for a single camera"""
    try:
        # Correct URL for GoPro API
        async with session.get(f"http://{camera_ip}:8080/gp/gpControl/command/mode?p=13", timeout=5) as response:
            if response.status != 200:
                logger.error(f"Failed to set timelapse mode for camera {camera_ip}. Status: {response.status}")
                return False
            
        # Wait for the mode to stabilize
        await asyncio.sleep(2)
        
        # Check the current mode
        async with session.get(f"http://{camera_ip}:8080/gp/gpControl/status", timeout=5) as status_response:
            if status_response.status == 200:
                status_data = await status_response.json()
                current_mode = status_data.get('status', {}).get('43')
                if current_mode == 13:  # 13 is the timelapse mode
                    logger.info(f"Timelapse mode set successfully for camera {camera_name}")
                    return True
                else:
                    logger.error(f"Failed to verify timelapse mode for camera {camera_name}. Current mode: {current_mode}")
                    return False
        
        return True
    except Exception as e:
        logger.error(f"Error setting timelapse mode for camera {camera_name}: {e}")
        return False

async def set_all_cameras_timelapse_mode_async(devices):
    """Asynchronously set timelapse mode for all cameras simultaneously"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for device in devices:
            task = set_timelapse_mode_async(session, device['ip'], device['name'])
            tasks.append(task)
        
        # Run all tasks simultaneously
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check results
        success = True
        for device, result in zip(devices, results):
            if isinstance(result, Exception):
                logger.error(f"Error setting timelapse mode for {device['name']}: {result}")
                success = False
            elif not result:
                success = False
        
        return success

def main():
    """Main function for running from GUI or command line"""
    try:
        check_dependencies()
        devices = discover_gopro_devices()
        if not devices:
            logger.error("No GoPro devices found")
            return False

        # Run asynchronous mode setting
        success = asyncio.run(set_all_cameras_timelapse_mode_async(devices))
        
        return success

    except Exception as e:
        logger.error(f"Error in timelapse_mode: {e}")
        return False

if __name__ == "__main__":
    main()