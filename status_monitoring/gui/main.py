import sys
import os
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gopro_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Получаем абсолютный путь к корневой директории проекта
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
    logger.debug(f"Added {ROOT_DIR} to sys.path")

logger.info("Starting GoPro Monitor application")

from PyQt5.QtWidgets import QApplication
try:
    logger.debug("Attempting to import StatusMonitorApp from package")
    from status_monitoring.gui.status_of_all_cameras import StatusMonitorApp
    logger.debug("Successfully imported StatusMonitorApp from package")
except ImportError as e:
    logger.warning(f"Failed to import from package: {e}")
    logger.debug("Attempting direct import")
    from status_of_all_cameras import StatusMonitorApp
    logger.debug("Successfully imported StatusMonitorApp directly")

def main():
    try:
        logger.info("Initializing QApplication")
        app = QApplication(sys.argv)
        
        logger.info("Creating main window")
        window = StatusMonitorApp()
        
        logger.info("Showing main window")
        window.show()
        
        logger.info("Starting event loop")
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 