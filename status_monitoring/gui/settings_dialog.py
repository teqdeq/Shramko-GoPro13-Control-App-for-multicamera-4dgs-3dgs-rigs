from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTabWidget, QWidget, QScrollArea, QGridLayout, QFrame)
from PyQt5.QtCore import Qt
import logging
from typing import Dict

class StatusSection(QFrame):
    """Section for displaying status information"""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(title_label)
        
        # Grid for status items
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        layout.addLayout(self.grid)
        
        self.row = 0
        
    def add_status_item(self, label: str, value: str = "--"):
        """Add a status item to the grid"""
        label_widget = QLabel(f"{label}:")
        value_widget = QLabel(value)
        value_widget.setObjectName(label.lower().replace(" ", "_"))
        
        self.grid.addWidget(label_widget, self.row, 0)
        self.grid.addWidget(value_widget, self.row, 1)
        self.row += 1
        
    def update_value(self, label: str, value: str):
        """Update value for a status item"""
        widget = self.findChild(QLabel, label.lower().replace(" ", "_"))
        if widget:
            widget.setText(value)

class SettingsDialog(QDialog):
    """Dialog for displaying camera settings and status"""
    
    def __init__(self, camera_id: str, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self.camera_id = camera_id
        self._setup_ui()
        
    def _setup_ui(self):
        """Initialize the UI components"""
        try:
            self.setWindowTitle(f"Camera {self.camera_id} Status")
            self.resize(600, 800)
            
            layout = QVBoxLayout(self)
            
            # Create tab widget
            tab_widget = QTabWidget()
            
            # Status tab
            status_tab = QWidget()
            status_layout = QVBoxLayout(status_tab)
            
            # System Status Section
            self.system_section = StatusSection("System Status")
            self.system_section.add_status_item("System State")
            self.system_section.add_status_item("Encoding State")
            self.system_section.add_status_item("USB Connection")
            self.system_section.add_status_item("Mode")
            status_layout.addWidget(self.system_section)
            
            # Hardware Status Section
            self.hardware_section = StatusSection("Hardware Status")
            self.hardware_section.add_status_item("Battery Level")
            self.hardware_section.add_status_item("Storage Remaining")
            self.hardware_section.add_status_item("Temperature")
            status_layout.addWidget(self.hardware_section)
            
            # Webcam Status Section
            self.webcam_section = StatusSection("Webcam Status")
            self.webcam_section.add_status_item("Preview State")
            self.webcam_section.add_status_item("Stream Status")
            self.webcam_section.add_status_item("Resolution")
            status_layout.addWidget(self.webcam_section)
            
            # Add status tab
            tab_widget.addTab(status_tab, "Status")
            
            # Add tab widget to main layout
            layout.addWidget(tab_widget)
            
        except Exception as e:
            self._logger.error(f"Error setting up UI: {str(e)}")
            
    def update_status(self, status: Dict):
        """Update displayed status information"""
        try:
            # Update system status
            self.system_section.update_value("system_state", 
                "Busy" if status.get("system_busy", False) else "Ready")
            self.system_section.update_value("encoding_state", 
                "Active" if status.get("encoding_active", False) else "Inactive")
            self.system_section.update_value("usb_connection", 
                "Connected" if status.get("usb_connected", False) else "Disconnected")
            self.system_section.update_value("mode", status.get("mode", "Unknown"))
            
            # Update hardware status
            self.hardware_section.update_value("battery_level", 
                f"{status.get('battery_level', '--')}%")
            self.hardware_section.update_value("storage_remaining", 
                f"{status.get('storage_remaining', '--')}%")
            self.hardware_section.update_value("temperature", 
                f"{status.get('temperature', '--')}°C")
            
            # Update webcam status
            webcam_status = status.get("webcam_status", {})
            self.webcam_section.update_value("preview_state", 
                webcam_status.get("state", "Inactive"))
            self.webcam_section.update_value("stream_status", 
                webcam_status.get("stream", "Stopped"))
            self.webcam_section.update_value("resolution", 
                webcam_status.get("resolution", "--"))
            
        except Exception as e:
            self._logger.error(f"Error updating status: {str(e)}")
            
    def closeEvent(self, event):
        """Handle dialog close event"""
        try:
            super().closeEvent(event)
        except Exception as e:
            self._logger.error(f"Error handling close event: {str(e)}") 