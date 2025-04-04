import sys
import os
import logging
from pathlib import Path
from utils import setup_logging, get_app_root, check_dependencies

def init_app() -> bool:
    """Application initialization
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        # Set the default encoding
        if sys.platform.startswith('win'):
            # For Windows, set UTF-8
            import locale
            if locale.getpreferredencoding().upper() != 'UTF-8':
                os.environ['PYTHONIOENCODING'] = 'utf-8'
                
        # Initialize logging
        logger = setup_logging('app_init')
        
        # Check dependencies
        check_dependencies()
        
        # Create necessary directories
        app_root = get_app_root()
        data_dir = app_root / 'data'
        presets_dir = data_dir / 'presets'
        logs_dir = app_root / 'logs'
        
        for directory in [data_dir, presets_dir, logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Check for required files
        required_files = [
            'prime_camera_sn.py',
            'goprolist_and_start_usb.py',
            'status_of_cameras_GUI.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not (app_root / file).exists():
                missing_files.append(file)
                
        if missing_files:
            logger.error(f"Missing required files: {', '.join(missing_files)}")
            return False
            
        logger.info("Application initialized successfully")
        return True
        
    except Exception as e:
        if 'logger' in locals():
            logger.error(f"Error initializing application: {e}")
        else:
            print(f"Error initializing application: {e}")
        return False

if __name__ == "__main__":
    init_app()