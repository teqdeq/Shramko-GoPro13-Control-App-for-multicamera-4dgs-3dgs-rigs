from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
import logging
from typing import Dict, Optional

from .preview_manager import PreviewStatus

class CameraCard(QFrame):
    """Widget displaying camera status and preview"""
    
    clicked = pyqtSignal(str)  # camera_id
    
    def __init__(self, camera_id: str):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self.camera_id = camera_id
        self.preview_enabled = False
        self._setup_ui()
        
    def _setup_ui(self):
        """Initialize the UI components"""
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        self.setMinimumSize(320, 240)
        
        # Create layout
        layout = QGridLayout()
        self.setLayout(layout)
        
        # Create preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setText("No Preview")
        self.preview_label.setMinimumSize(300, 200)
        layout.addWidget(self.preview_label, 0, 0, 1, 2)
        
        # Create status labels
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.status_label, 1, 0)
        
        self.battery_label = QLabel()
        self.battery_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.battery_label, 2, 0)
        
        self.storage_label = QLabel()
        self.storage_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.storage_label, 3, 0)
        
        # Set initial text
        self.status_label.setText("Status: Unknown")
        self.battery_label.setText("Battery: Unknown")
        self.storage_label.setText("Storage: Unknown")
        
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.camera_id)
            
    def update_preview(self, image: QImage):
        """Update preview image"""
        if self.preview_enabled:
            pixmap = QPixmap.fromImage(image)
            scaled = pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(scaled)
            
    def update_status(self, state: Dict):
        """Update status display"""
        try:
            # Update status
            status_text = "Status: "
            if state.get("system_busy", False):
                status_text += "Busy"
            elif state.get("encoding_active", False):
                status_text += "Recording"
            else:
                status_text += "Ready"
            self.status_label.setText(status_text)
            
            # Update battery
            battery = state.get("battery_level", 0)
            self.battery_label.setText(f"Battery: {battery}%")
            
            # Update storage
            remaining = state.get("storage_remaining", 0)
            total = state.get("storage_total", 0)
            if total > 0:
                percent = (remaining / total) * 100
                self.storage_label.setText(f"Storage: {remaining:.1f}GB / {total:.1f}GB ({percent:.1f}%)")
            else:
                self.storage_label.setText("Storage: Unknown")
                
        except Exception as e:
            self._logger.error(f"Error updating status: {str(e)}")
            
    def set_preview_enabled(self, enabled: bool):
        """Enable/disable preview"""
        self.preview_enabled = enabled
        if not enabled:
            self.preview_label.setText("No Preview")

class CameraGrid(QWidget):
    """Grid of camera status cards"""
    
    camera_clicked = pyqtSignal(str)  # camera_id
    
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self.cards: Dict[str, CameraCard] = {}
        self.preview_enabled = False
        self._setup_ui()
        
    def _setup_ui(self):
        """Initialize the UI components"""
        self.layout = QGridLayout()
        self.layout.setSpacing(10)
        self.setLayout(self.layout)
        
    def add_camera(self, camera_id: str):
        """Add a new camera card"""
        try:
            if camera_id not in self.cards:
                card = CameraCard(camera_id)
                card.clicked.connect(self.camera_clicked)
                self.cards[camera_id] = card
                self._update_layout()
                
        except Exception as e:
            self._logger.error(f"Error adding camera {camera_id}: {str(e)}")
            
    def remove_camera(self, camera_id: str):
        """Remove a camera card"""
        try:
            if camera_id in self.cards:
                card = self.cards.pop(camera_id)
                self.layout.removeWidget(card)
                card.deleteLater()
                self._update_layout()
                
        except Exception as e:
            self._logger.error(f"Error removing camera {camera_id}: {str(e)}")
            
    def update_camera_preview(self, camera_id: str, image: QImage):
        """Update preview for a camera"""
        try:
            if camera_id in self.cards:
                self.cards[camera_id].update_preview(image)
                
        except Exception as e:
            self._logger.error(f"Error updating preview for camera {camera_id}: {str(e)}")
            
    def update_camera_status(self, camera_id: str, state: Dict):
        """Update status for a camera"""
        try:
            if camera_id in self.cards:
                # Format storage values
                remaining_gb = state["storage_remaining"] / (1024 * 1024 * 1024)
                total_gb = state["storage_total"] / (1024 * 1024 * 1024)
                used_percent = int((1 - remaining_gb / total_gb) * 100) if total_gb > 0 else 0
                
                # Update status text
                status_text = f"Status: {'Busy' if state.get('system_busy', False) else 'Ready'}"
                battery_text = f"Battery: {state.get('battery_level', 0)}%"
                storage_text = f"Storage: {remaining_gb:.1f}GB / {total_gb:.1f}GB ({used_percent}% used)"
                
                # Update card labels
                self.cards[camera_id].status_label.setText(status_text)
                self.cards[camera_id].battery_label.setText(battery_text)
                self.cards[camera_id].storage_label.setText(storage_text)
                
        except Exception as e:
            self._logger.error(f"Error updating status for camera {camera_id}: {str(e)}")
            
    def set_preview_enabled(self, enabled: bool):
        """Enable/disable preview for all cameras"""
        try:
            self.preview_enabled = enabled
            for card in self.cards.values():
                card.set_preview_enabled(enabled)
                
        except Exception as e:
            self._logger.error(f"Error setting preview enabled: {str(e)}")
            
    def _update_layout(self):
        """Update grid layout"""
        try:
            # Remove all widgets
            for i in reversed(range(self.layout.count())): 
                self.layout.itemAt(i).widget().setParent(None)
                
            # Calculate grid dimensions
            count = len(self.cards)
            cols = max(1, min(3, count))  # Max 3 columns
            rows = (count + cols - 1) // cols
            
            # Add cards to grid
            for i, card in enumerate(self.cards.values()):
                row = i // cols
                col = i % cols
                self.layout.addWidget(card, row, col)
                
        except Exception as e:
            self._logger.error(f"Error updating layout: {str(e)}") 