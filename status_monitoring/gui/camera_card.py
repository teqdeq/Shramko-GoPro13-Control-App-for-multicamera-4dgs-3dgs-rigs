from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
import logging
from typing import Dict, Optional

class CameraCard(QFrame):
    """Widget displaying status of a single HERO13 camera"""
    
    clicked = pyqtSignal(str)  # Signal when card is clicked
    error_occurred = pyqtSignal(str, str)  # Signal for errors
    
    def __init__(self, camera_id: str, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self.camera_id = camera_id
        self.preview_enabled = False
        self._setup_ui()
        
    def _setup_ui(self):
        """Initialize the UI components"""
        try:
            # Set up frame
            self.setFrameStyle(QFrame.Box | QFrame.Raised)
            self.setLineWidth(2)
            self.setMinimumSize(200, 300)
            
            # Create layout
            layout = QVBoxLayout(self)
            layout.setSpacing(5)
            layout.setContentsMargins(5, 5, 5, 5)
            
            # Camera ID label
            self.id_label = QLabel(f"Camera {self.camera_id}")
            self.id_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.id_label)
            
            # Preview image
            self.preview_label = QLabel()
            self.preview_label.setAlignment(Qt.AlignCenter)
            self.preview_label.setMinimumSize(160, 120)
            layout.addWidget(self.preview_label)
            
            # Status indicators
            self.status_layout = QVBoxLayout()
            
            # System busy indicator
            self.busy_label = QLabel("System: Ready")
            self.busy_label.setStyleSheet("color: green")
            self.status_layout.addWidget(self.busy_label)
            
            # Encoding indicator
            self.encoding_label = QLabel("Encoding: No")
            self.encoding_label.setStyleSheet("color: gray")
            self.status_layout.addWidget(self.encoding_label)
            
            # Battery level
            self.battery_label = QLabel("Battery: --")
            self.status_layout.addWidget(self.battery_label)
            
            # Storage remaining
            self.storage_label = QLabel("Storage: --")
            self.status_layout.addWidget(self.storage_label)
            
            # Temperature
            self.temp_label = QLabel("Temp: --")
            self.status_layout.addWidget(self.temp_label)
            
            # USB status
            self.usb_label = QLabel("USB: --")
            self.status_layout.addWidget(self.usb_label)
            
            layout.addLayout(self.status_layout)
            
        except Exception as e:
            self._logger.error(f"Error setting up UI: {str(e)}")
            
    def mousePressEvent(self, event):
        """Handle mouse click events"""
        self.clicked.emit(self.camera_id)
        
    def update_status(self, status: Dict):
        """Update displayed status information"""
        try:
            # Update system busy status
            if status.get("system_busy", False):
                self.busy_label.setText("System: Busy")
                self.busy_label.setStyleSheet("color: red")
            else:
                self.busy_label.setText("System: Ready")
                self.busy_label.setStyleSheet("color: green")
                
            # Update encoding status    
            if status.get("encoding_active", False):
                self.encoding_label.setText("Encoding: Yes")
                self.encoding_label.setStyleSheet("color: orange")
            else:
                self.encoding_label.setText("Encoding: No")
                self.encoding_label.setStyleSheet("color: gray")
                
            # Update other status indicators
            self.battery_label.setText(f"Battery: {status.get('battery_level', '--')}%")
            self.storage_label.setText(f"Storage: {status.get('storage_remaining', '--')}%")
            self.temp_label.setText(f"Temp: {status.get('temperature', '--')}°C")
            
            # Update USB status
            usb_status = "Connected" if status.get("usb_connected", False) else "Disconnected"
            self.usb_label.setText(f"USB: {usb_status}")
            
            # Handle errors
            if status.get("error_message"):
                self.error_occurred.emit(self.camera_id, status["error_message"])
                
        except Exception as e:
            self._logger.error(f"Error updating status: {str(e)}")
            
    def update_preview(self, image: Optional[QImage]):
        """Update preview image"""
        try:
            if image and not image.isNull():
                pixmap = QPixmap.fromImage(image)
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
            else:
                self.preview_label.clear()
                
        except Exception as e:
            self._logger.error(f"Error updating preview: {str(e)}")
            
    def set_preview_enabled(self, enabled: bool):
        """Enable or disable preview"""
        try:
            self.preview_enabled = enabled
            if not enabled:
                self.preview_label.clear()
                
        except Exception as e:
            self._logger.error(f"Error setting preview state: {str(e)}")
            
    def set_size(self, width: int, height: int):
        """Set card size"""
        try:
            self.setFixedSize(width, height)
            
        except Exception as e:
            self._logger.error(f"Error setting size: {str(e)}")
            
    def _set_error_state(self, error_message: str):
        """Set error state for the card"""
        try:
            self.setStyleSheet("QFrame { border: 2px solid red; }")
            self.error_occurred.emit(self.camera_id, error_message)
            
        except Exception as e:
            self._logger.error(f"Error setting error state: {str(e)}")
            
    def _clear_error_state(self):
        """Clear error state"""
        try:
            self.setStyleSheet("")
            
        except Exception as e:
            self._logger.error(f"Error clearing error state: {str(e)}") 