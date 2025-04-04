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

async def set_photo_mode_async(session, camera_ip, camera_name):
    """Asynchronously set photo mode for a single camera"""
    try:
        # Correct URL for GoPro API
        async with session.get(f"http://{camera_ip}:8080/gp/gpControl/command/mode?p=1", timeout=5) as response:
            if response.status == 200:
                logger.info(f"Photo mode command sent successfully to camera {camera_name}")
                return True
            elif response.status == 500:
                logger.info(f"Camera {camera_name} already in requested mode")
                return True
            else:
                logger.error(f"Failed to set photo mode for camera {camera_ip}. Status: {response.status}")
                return False
            
    except Exception as e:
        logger.error(f"Error setting photo mode for camera {camera_name}: {e}")
        return False

async def set_all_cameras_photo_mode_async(devices):
    """Asynchronously set photo mode for all cameras simultaneously"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for device in devices:
            task = set_photo_mode_async(session, device['ip'], device['name'])
            tasks.append(task)
        
        # Run all tasks simultaneously
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check results
        success = True
        for device, result in zip(devices, results):
            if isinstance(result, Exception):
                logger.error(f"Error setting photo mode for {device['name']}: {result}")
                success = False
            elif not result:
                success = False
        
        return success  # Return True if commands were sent successfully

def main():
    """Main function for running from GUI or command line"""
    try:
        check_dependencies()
        devices = discover_gopro_devices()
        if not devices:
            logger.error("No GoPro devices found")
            return False

        # Run asynchronous mode setting
        success = asyncio.run(set_all_cameras_photo_mode_async(devices))
        
        return success

    except Exception as e:
        logger.error(f"Error in photo_mode: {e}")
        return False

if __name__ == "__main__":
    main()