import ctypes
import logging
from contextlib import contextmanager
import os

logger = logging.getLogger(__name__)

# Windows constants
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
ES_AWAYMODE_REQUIRED = 0x00000040

class PowerManager:
    def __init__(self):
        self.previous_state = None
        
    def prevent_sleep(self):
        """Prevents the computer from entering sleep mode"""
        try:
            # For Windows
            if hasattr(ctypes, 'windll'):
                mode = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
                ctypes.windll.kernel32.SetThreadExecutionState(mode)
                logger.info("Sleep prevention enabled (Windows)")
            # For Linux
            elif os.path.exists('/usr/bin/xdg-screensaver'):
                os.system('xdg-screensaver suspend $$')
                logger.info("Sleep prevention enabled (Linux)")
            # For macOS
            elif os.path.exists('/usr/bin/caffeinate'):
                os.system('caffeinate -d -i &')
                logger.info("Sleep prevention enabled (macOS)")
                
        except Exception as e:
            logger.error(f"Failed to prevent sleep mode: {e}")
            
    def allow_sleep(self):
        """Restores the system to normal power-saving mode"""
        try:
            # For Windows
            if hasattr(ctypes, 'windll'):
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
                logger.info("Sleep prevention disabled (Windows)")
            # For Linux
            elif os.path.exists('/usr/bin/xdg-screensaver'):
                os.system('xdg-screensaver resume $$')
                logger.info("Sleep prevention disabled (Linux)")
            # For macOS
            elif os.path.exists('/usr/bin/caffeinate'):
                os.system('pkill caffeinate')
                logger.info("Sleep prevention disabled (macOS)")
                
        except Exception as e:
            logger.error(f"Failed to restore sleep mode: {e}")

    @contextmanager
    def prevent_system_sleep(self):
        """Context manager for temporarily preventing sleep"""
        try:
            self.prevent_sleep()
            yield
        finally:
            self.allow_sleep()