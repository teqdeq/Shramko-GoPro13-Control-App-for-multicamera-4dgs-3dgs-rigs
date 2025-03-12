import sys
import os
import logging
from PyQt5.QtWidgets import QApplication

# Add status_monitoring directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

def main():
    """Main entry point"""
    try:
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(__name__)
        logger.info("Starting GoPro Monitor application")
        
        # Create application
        app = QApplication(sys.argv)
        
        # Import here to avoid circular imports
        from gui.status_of_all_cameras import StatusMonitorApp
        
        # Create and show main window
        window = StatusMonitorApp()
        window.show()
        
        # Start event loop
        sys.exit(app.exec_())
        
    except ImportError as e:
        logger.error(f"Failed to import StatusMonitorApp: {str(e)}")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")

if __name__ == '__main__':
    main() 