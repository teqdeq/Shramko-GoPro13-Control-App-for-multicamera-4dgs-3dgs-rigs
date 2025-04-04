import os
import sys
import logging
from pathlib import Path
from datetime import datetime

def get_app_root() -> Path:
    """Get the root directory of the application"""
    if getattr(sys, 'frozen', False):
        # For compiled applications
        return Path(sys.executable).parent
    else:
        # For development
        return Path(__file__).parent

def get_data_dir() -> Path:
    """Get the directory for data"""
    data_dir = get_app_root() / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def get_logs_dir() -> Path:
    """Get the directory for logs"""
    logs_dir = get_app_root() / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

def setup_logging(name: str = None) -> logging.Logger:
    """Set up logging
    
    Args:
        name: Logger name (optional)
    
    Returns:
        logging.Logger: Configured logger
    """
    # Create the directory for logs
    logs_dir = get_logs_dir()
    
    # Generate the log file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"gopro_control_{timestamp}.log"
    
    # Get or create the logger
    logger = logging.getLogger(name) if name else logging.getLogger()
    
    # If the logger is already configured, return it
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG)
    
    # Formatter for logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def check_dependencies():
    """Check for required dependencies"""
    try:
        import PyQt5
        import requests
        import humanize
        import zeroconf
    except ImportError as e:
        logging.error(f"Missing dependency: {e}")
        raise

def ensure_dir(path: Path):
    """Create a directory if it does not exist"""
    path.mkdir(parents=True, exist_ok=True)