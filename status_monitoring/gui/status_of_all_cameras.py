from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QToolBar, QAction, QMessageBox
from PyQt5.QtCore import Qt, QTimer
import logging
from typing import Dict, Optional
import json
import os
import sys

# Import existing functionality
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from goprolist_and_start_usb import discover_gopro_devices

# Import monitoring components
from status_monitoring.gui.camera_grid import CameraGrid
from status_monitoring.gui.settings_dialog import SettingsDialog
from status_monitoring.gui.preview_manager import PreviewManager, PreviewStatus
from status_monitoring.core.camera_status import CameraStatusManager

class StatusMonitorApp(QMainWindow):
    """Main application window for monitoring HERO13 cameras via USB"""
    
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self.cameras: Dict[str, CameraStatusManager] = {}
        self.settings_dialogs: Dict[str, SettingsDialog] = {}
        self._setup_ui()
        
        # Use existing functionality for camera discovery
        try:
            self._logger.info("Discovering GoPro cameras...")
            discovered_cameras = discover_gopro_devices()
            
            for camera in discovered_cameras:
                camera_id = camera['name'].split('.')[0]  # Get ID from name
                camera_ip = camera['ip']
                
                # Add camera for monitoring
                self._add_camera(camera_id, camera_ip)
                self._logger.info(f"Added camera {camera_id} at {camera_ip}")
                    
        except Exception as e:
            self._logger.error(f"Error during camera discovery: {str(e)}")
            
        # Setup timers after camera initialization
        self._setup_timers()
            
    def _setup_ui(self):
        """Initialize the UI components"""
        try:
            self.setWindowTitle("GoPro HERO13 Status Monitor")
            self.resize(1200, 800)
            
            # Create central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            
            # Create toolbar
            toolbar = QToolBar()
            self.addToolBar(toolbar)
            
            # Add actions
            refresh_action = QAction("Refresh", self)
            refresh_action.triggered.connect(self._refresh_all_cameras)
            toolbar.addAction(refresh_action)
            
            preview_action = QAction("Toggle Preview", self)
            preview_action.triggered.connect(self._toggle_preview)
            toolbar.addAction(preview_action)
            
            # Create camera grid
            self.camera_grid = CameraGrid()
            self.camera_grid.camera_clicked.connect(self._show_camera_settings)
            layout.addWidget(self.camera_grid)
            
            # Create preview manager
            self.preview_manager = PreviewManager()
            self.preview_manager.preview_updated.connect(self.camera_grid.update_camera_preview)
            self.preview_manager.status_changed.connect(self._handle_preview_status)
            
        except Exception as e:
            self._logger.error(f"Error setting up UI: {str(e)}")
            
    def _setup_timers(self):
        """Setup update timers"""
        try:
            # Status update timer (every 1 second)
            self.status_timer = QTimer(self)
            self.status_timer.timeout.connect(self._update_all_cameras)
            self.status_timer.start(1000)
            
        except Exception as e:
            self._logger.error(f"Error setting up timers: {str(e)}")
            
    def _add_camera(self, camera_id: str, camera_ip: str):
        """Add a new camera to monitor"""
        try:
            if camera_id not in self.cameras:
                # Create camera status manager
                camera = CameraStatusManager(camera_ip)
                self.cameras[camera_id] = camera
                
                # Add to grid
                self.camera_grid.add_camera(camera_id)
                
        except Exception as e:
            self._logger.error(f"Error adding camera {camera_id}: {str(e)}")
            
    def _remove_camera(self, camera_id: str):
        """Remove a camera from monitoring"""
        try:
            if camera_id in self.cameras:
                # Stop preview if active
                self.preview_manager.stop_preview(camera_id)
                
                # Remove from grid
                self.camera_grid.remove_camera(camera_id)
                
                # Remove status manager
                del self.cameras[camera_id]
                
                # Close settings dialog if open
                if camera_id in self.settings_dialogs:
                    self.settings_dialogs[camera_id].close()
                    del self.settings_dialogs[camera_id]
                    
        except Exception as e:
            self._logger.error(f"Error removing camera {camera_id}: {str(e)}")
            
    def _update_all_cameras(self):
        """Update status for all cameras"""
        try:
            for camera_id, camera in self.cameras.items():
                if camera.update_state():
                    # Update grid
                    self.camera_grid.update_camera_status(camera_id, camera.get_state_dict())
                    
                    # Update settings dialog if open
                    if camera_id in self.settings_dialogs:
                        self.settings_dialogs[camera_id].update_status(camera.get_state_dict())
                        
        except Exception as e:
            self._logger.error(f"Error updating cameras: {str(e)}")
            
    def _refresh_all_cameras(self):
        """Manually refresh all cameras"""
        try:
            self._update_all_cameras()
            
        except Exception as e:
            self._logger.error(f"Error refreshing cameras: {str(e)}")
            
    def _toggle_preview(self):
        """Toggle preview for all cameras"""
        try:
            # Get current preview state
            enabled = not self.camera_grid.preview_enabled
            
            # Update grid
            self.camera_grid.set_preview_enabled(enabled)
            
            # Start/stop previews
            if enabled:
                for camera_id, camera in self.cameras.items():
                    if camera.start_preview():
                        self.preview_manager.start_preview(camera_id, camera.camera_ip)
            else:
                self.preview_manager.stop_all_previews()
                for camera_id, camera in self.cameras.items():
                    camera.stop_preview()
                
        except Exception as e:
            self._logger.error(f"Error toggling preview: {str(e)}")
            
    def _show_camera_settings(self, camera_id: str):
        """Show settings dialog for camera"""
        try:
            if camera_id not in self.settings_dialogs:
                dialog = SettingsDialog(camera_id, self)
                self.settings_dialogs[camera_id] = dialog
                
                # Update with current status
                if camera_id in self.cameras:
                    dialog.update_status(self.cameras[camera_id].get_state_dict())
                    
            self.settings_dialogs[camera_id].show()
            self.settings_dialogs[camera_id].raise_()
            
        except Exception as e:
            self._logger.error(f"Error showing settings for camera {camera_id}: {str(e)}")
            
    def _handle_preview_status(self, camera_id: str, status: PreviewStatus):
        """Handle preview status change"""
        try:
            if status == PreviewStatus.ERROR:
                QMessageBox.warning(self, "Preview Error", 
                    f"Failed to start preview for camera {camera_id}")
            
        except Exception as e:
            self._logger.error(f"Error handling preview status: {str(e)}")
            
    def closeEvent(self, event):
        """Handle application close"""
        try:
            # Stop all previews
            self.preview_manager.stop_all_previews()
            for camera_id, camera in self.cameras.items():
                camera.stop_preview()
            
            # Stop timers
            self.status_timer.stop()
            
            # Close all dialogs
            for dialog in self.settings_dialogs.values():
                dialog.close()
                
            super().closeEvent(event)
            
        except Exception as e:
            self._logger.error(f"Error handling close event: {str(e)}")
            event.accept() 