import logging
import os
from datetime import datetime
from typing import Optional

class Logger:
    """Logging manager"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"monitor_{timestamp}.log")
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("GoPro Monitor")
        
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
        
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
        
    def error(self, message: str, exc: Optional[Exception] = None):
        """Log error message"""
        if exc:
            self.logger.error(f"{message}: {str(exc)}")
        else:
            self.logger.error(message)
            
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
        
    def camera_status(self, camera_id: str, status: str):
        """Log camera status change"""
        self.info(f"Camera {camera_id} status: {status}")
        
    def camera_error(self, camera_id: str, error: str):
        """Log camera error"""
        self.error(f"Camera {camera_id} error: {error}")
        
    def preview_status(self, camera_id: str, status: str):
        """Log preview status change"""
        self.info(f"Camera {camera_id} preview: {status}")
        
    def connection_status(self, camera_id: str, connected: bool):
        """Log connection status change"""
        status = "connected" if connected else "disconnected"
        self.info(f"Camera {camera_id} {status}")
        
    def settings_change(self, camera_id: str, setting: str, value: str):
        """Log settings change"""
        self.info(f"Camera {camera_id} setting changed: {setting} = {value}")
        
    def transfer_status(self, camera_id: str, status: str):
        """Log transfer status"""
        self.info(f"Camera {camera_id} transfer: {status}")
        
    def system_status(self, message: str):
        """Log system status"""
        self.info(f"System: {message}")
        
    def cleanup(self):
        """Cleanup old log files"""
        try:
            # Keep only last 7 days of logs
            current_time = datetime.now().timestamp()
            for filename in os.listdir(self.log_dir):
                filepath = os.path.join(self.log_dir, filename)
                if os.path.getmtime(filepath) < current_time - (7 * 24 * 60 * 60):
                    os.remove(filepath)
        except Exception as e:
            self.error("Error cleaning up logs", e) 