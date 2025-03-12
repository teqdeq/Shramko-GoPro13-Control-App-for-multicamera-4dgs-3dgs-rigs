from enum import Enum, auto
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtGui import QImage
import cv2
import numpy as np
import logging
from typing import Dict, Optional
import requests
import time

class PreviewStatus(Enum):
    """Preview status"""
    INACTIVE = 0
    STARTING = 1 
    ACTIVE = 2
    ERROR = 3

class PreviewWorker(QThread):
    """Worker thread for handling camera preview"""
    
    preview_updated = pyqtSignal(str, QImage)  # camera_id, image
    status_changed = pyqtSignal(str, PreviewStatus)  # camera_id, status
    
    def __init__(self, camera_id: str, camera_ip: str):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self.camera_id = camera_id
        self.camera_ip = camera_ip
        self.running = False
        self.status = PreviewStatus.INACTIVE
        
    def run(self):
        """Main worker loop"""
        try:
            self.running = True
            self.status = PreviewStatus.STARTING
            self.status_changed.emit(self.camera_id, self.status)

            # Start preview stream
            response = requests.get(f"http://{self.camera_ip}:8080/gopro/camera/stream/start", timeout=2)
            if response.status_code != 200:
                self._logger.error(f"Failed to start stream: {response.status_code}")
                self.status = PreviewStatus.ERROR
                self.status_changed.emit(self.camera_id, self.status)
                return

            # Open video stream
            cap = cv2.VideoCapture(f"udp://{self.camera_ip}:8554")
            if not cap.isOpened():
                self._logger.error("Failed to open video capture")
                self.status = PreviewStatus.ERROR
                self.status_changed.emit(self.camera_id, self.status)
                return
                
            self.status = PreviewStatus.ACTIVE
            self.status_changed.emit(self.camera_id, self.status)
            
            last_frame_time = time.time()
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    if time.time() - last_frame_time > 5:  # 5 second timeout
                        self._logger.warning("Preview timeout")
                        break
                    continue
                    
                last_frame_time = time.time()
                
                # Convert frame to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert frame to QImage
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
                self.preview_updated.emit(self.camera_id, q_image)
                
                # Small delay to prevent high CPU usage
                time.sleep(0.03)  # ~30 FPS
                
            cap.release()
            
            # Stop preview stream
            requests.get(f"http://{self.camera_ip}:8080/gopro/camera/stream/stop", timeout=2)
            
        except Exception as e:
            self._logger.error(f"Preview worker error: {str(e)}")
            self.status = PreviewStatus.ERROR
            self.status_changed.emit(self.camera_id, self.status)
            
        finally:
            self.running = False
            self.status = PreviewStatus.INACTIVE
            self.status_changed.emit(self.camera_id, self.status)
            
    def stop(self):
        """Stop the preview worker"""
        self.running = False
        self.wait()

class PreviewManager(QObject):
    """Manages preview streams for multiple cameras"""
    
    preview_updated = pyqtSignal(str, QImage)  # camera_id, image
    status_changed = pyqtSignal(str, PreviewStatus)  # camera_id, status
    
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self.workers: Dict[str, PreviewWorker] = {}
        
    def start_preview(self, camera_id: str, camera_ip: str):
        """Start preview for a camera"""
        try:
            if camera_id in self.workers:
                self._logger.warning(f"Preview already active for camera {camera_id}")
                return
                
            worker = PreviewWorker(camera_id, camera_ip)
            worker.preview_updated.connect(lambda cid, img: self.preview_updated.emit(cid, img))
            worker.status_changed.connect(lambda cid, status: self.status_changed.emit(cid, status))
            
            self.workers[camera_id] = worker
            worker.start()
            
        except Exception as e:
            self._logger.error(f"Error starting preview for camera {camera_id}: {str(e)}")
            
    def stop_preview(self, camera_id: str):
        """Stop preview for a camera"""
        try:
            if camera_id in self.workers:
                worker = self.workers.pop(camera_id)
                worker.stop()
                
        except Exception as e:
            self._logger.error(f"Error stopping preview for camera {camera_id}: {str(e)}")
            
    def stop_all_previews(self):
        """Stop all active previews"""
        try:
            for camera_id in list(self.workers.keys()):
                self.stop_preview(camera_id)
                
        except Exception as e:
            self._logger.error(f"Error stopping all previews: {str(e)}")
            
    def is_preview_active(self, camera_id: str) -> bool:
        """Check if preview is active for a camera"""
        return camera_id in self.workers 