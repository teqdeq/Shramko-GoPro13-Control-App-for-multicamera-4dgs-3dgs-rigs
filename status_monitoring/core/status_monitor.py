import asyncio
from typing import Dict, List, Optional
import aiohttp
import logging
from dataclasses import dataclass
from enum import Enum

class WebcamStatus(Enum):
    OFF = "Off"
    ACTIVE = "Active"
    ERROR = "Error"
    PREVIEW = "Preview"

@dataclass
class CameraStatus:
    camera_id: str
    battery_level: int
    storage_free: int
    storage_total: int
    usb_status: str
    current_mode: str
    is_recording: bool
    current_settings: Dict
    temperature: float
    connection_status: str
    system_busy: bool
    encoding_active: bool
    webcam_status: WebcamStatus = WebcamStatus.OFF
    keep_alive_timestamp: float = 0

class CameraStatusMonitor:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._cameras: Dict[str, CameraStatus] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._monitoring = False
        self._webcam_sessions: Dict[str, bool] = {}
        
    async def start_monitoring(self, camera_ips: List[str]):
        """Start monitoring all cameras"""
        try:
            self._monitoring = True
            self._session = aiohttp.ClientSession(headers={
                'Accept': 'application/json',
                'Connection': 'Keep-Alive'
            })
            
            while self._monitoring:
                tasks = []
                for ip in camera_ips:
                    tasks.append(self.update_camera_status(ip))
                await asyncio.gather(*tasks)
                await asyncio.sleep(1)  # Update every second
                
                # Send keep-alive to maintain connection
                for ip in camera_ips:
                    try:
                        await self._send_keep_alive(ip)
                        if ip in self._cameras:
                            self._cameras[ip].keep_alive_timestamp = asyncio.get_event_loop().time()
                    except Exception as e:
                        self._logger.error(f"Keep-alive failed for camera {ip}: {str(e)}")
                        
        except Exception as e:
            self._logger.error(f"Error in monitoring loop: {str(e)}")
            raise
            
    async def stop_monitoring(self):
        """Stop monitoring all cameras"""
        try:
            self._monitoring = False
            # Exit webcam mode for all active webcam sessions
            for ip, is_active in self._webcam_sessions.items():
                if is_active:
                    try:
                        await self.exit_webcam_mode(ip)
                    except Exception as e:
                        self._logger.error(f"Error exiting webcam mode for {ip}: {str(e)}")
            
            if self._session:
                await self._session.close()
        except Exception as e:
            self._logger.error(f"Error stopping monitoring: {str(e)}")
            
    async def update_camera_status(self, camera_ip: str):
        """Update status for a single camera"""
        try:
            # Get complete camera state
            state = await self._get_camera_state(camera_ip)
            
            # Extract status information from state
            status = state.get('status', {})
            settings = state.get('settings', {})
            
            self._cameras[camera_ip] = CameraStatus(
                camera_id=camera_ip,
                battery_level=status.get('1', 0),  # Battery level
                storage_free=status.get('54', 0),  # Storage remaining
                storage_total=status.get('53', 0),  # Storage total
                usb_status=status.get('109', 'disconnected'),  # USB status
                current_mode=settings.get('144', 'unknown'),  # Current mode
                is_recording=status.get('8', False),  # Encoding active
                current_settings=settings,
                temperature=status.get('57', 0.0),  # Internal temp
                connection_status='connected',
                system_busy=status.get('89', False),  # System busy
                encoding_active=status.get('8', False),  # Encoding active
                webcam_status=self._webcam_sessions.get(camera_ip, WebcamStatus.OFF),
                keep_alive_timestamp=self._cameras.get(camera_ip, CameraStatus(
                    camera_id=camera_ip, battery_level=0, storage_free=0, 
                    storage_total=0, usb_status='', current_mode='', 
                    is_recording=False, current_settings={}, temperature=0.0,
                    connection_status='', system_busy=False, encoding_active=False
                )).keep_alive_timestamp
            )
            
            # Check if system is ready for commands
            if self._cameras[camera_ip].system_busy:
                self._logger.warning(f"Camera {camera_ip} is busy, some commands may be rejected")
            if self._cameras[camera_ip].encoding_active:
                self._logger.warning(f"Camera {camera_ip} is recording, settings cannot be changed")
                
        except Exception as e:
            self._logger.error(f"Error updating camera {camera_ip}: {str(e)}")
            if camera_ip in self._cameras:
                self._cameras[camera_ip].connection_status = 'error'

    async def _get_camera_state(self, camera_ip: str) -> Dict:
        """Get complete camera state according to API docs"""
        try:
            async with self._session.get(f'http://{camera_ip}:8080/gopro/camera/state') as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get camera state: {response.status}")
        except Exception as e:
            self._logger.error(f"Error getting camera state: {str(e)}")
            raise

    async def _send_keep_alive(self, camera_ip: str):
        """Send keep-alive signal to maintain connection"""
        try:
            async with self._session.get(f'http://{camera_ip}:8080/gp/gpControl/command/keep_alive') as response:
                if response.status != 200:
                    raise Exception(f"Keep-alive failed: {response.status}")
        except Exception as e:
            self._logger.error(f"Error sending keep-alive: {str(e)}")
            raise

    async def enter_webcam_preview(self, camera_ip: str):
        """Enter webcam preview mode"""
        try:
            async with self._session.get(f'http://{camera_ip}:8080/gopro/webcam/preview') as response:
                if response.status == 200:
                    self._webcam_sessions[camera_ip] = True
                    if camera_ip in self._cameras:
                        self._cameras[camera_ip].webcam_status = WebcamStatus.PREVIEW
                else:
                    raise Exception(f"Failed to enter webcam preview: {response.status}")
        except Exception as e:
            self._logger.error(f"Error entering webcam preview: {str(e)}")
            if camera_ip in self._cameras:
                self._cameras[camera_ip].webcam_status = WebcamStatus.ERROR
            raise

    async def exit_webcam_mode(self, camera_ip: str):
        """Exit webcam mode"""
        try:
            async with self._session.get(f'http://{camera_ip}:8080/gopro/webcam/exit') as response:
                if response.status == 200:
                    self._webcam_sessions[camera_ip] = False
                    if camera_ip in self._cameras:
                        self._cameras[camera_ip].webcam_status = WebcamStatus.OFF
                else:
                    raise Exception(f"Failed to exit webcam mode: {response.status}")
        except Exception as e:
            self._logger.error(f"Error exiting webcam mode: {str(e)}")
            raise

    def get_camera_status(self, camera_ip: str) -> Optional[CameraStatus]:
        """Get current status for a camera"""
        return self._cameras.get(camera_ip)

    def get_all_cameras_status(self) -> Dict[str, CameraStatus]:
        """Get status for all cameras"""
        return self._cameras.copy()

    def is_camera_ready(self, camera_ip: str) -> bool:
        """Check if camera is ready to accept commands"""
        if camera_ip not in self._cameras:
            return False
        camera = self._cameras[camera_ip]
        return not (camera.system_busy or camera.encoding_active) 