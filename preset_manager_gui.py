from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QMessageBox, QInputDialog, QLabel,
    QFrame, QTextEdit, QSplitter, QWidget, QTabWidget,
    QApplication, QTableWidget, QTableWidgetItem, QMainWindow
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os
import json
from pathlib import Path
import logging
from utils import setup_logging
from goprolist_and_start_usb import discover_gopro_devices
from progress_dialog import SettingsProgressDialog
from read_and_write_all_settings_from_prime_to_other_v02 import (
    get_primary_camera_serial, is_prime_camera, get_camera_settings,
    copy_camera_settings_sync, USB_HEADERS, wait_for_camera_ready, get_camera_status,
    apply_setting, group_settings_by_priority, DELAYS
)
from mode_switcher import ModeSwitcher
from datetime import datetime
import requests
import time
from camera_settings_manager import CameraSettingsManager

# Define settings by mode
MODE_SETTINGS = {
    'video': {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30},
    'photo': {125, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175},
    'timelapse': {31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45}
}

# Template file prefixes
MODE_PREFIXES = {
    'video': 'video_',
    'photo': 'photo_',
    'timelapse': 'timelapse_'
}

setup_logging()
logger = logging.getLogger(__name__)

class PresetManagerDialog(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Preset Manager')
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create templates directory if it doesn't exist
        current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.templates_dir = current_dir / 'camera_templates'
        self.templates_dir.mkdir(exist_ok=True)
        logger.info(f"Templates directory: {self.templates_dir}")
        
        # Load settings descriptions
        self.load_settings_descriptions()
        
        # Initialize widget dictionaries ONLY ONCE
        self.list_widgets = {}
        self.settings_displays = {}
        logger.info("Initialized widget dictionaries")
        
        # Add mode switcher
        self.mode_switcher = ModeSwitcher(self)
        main_layout.addWidget(self.mode_switcher)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Tabs for different modes
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)  # Устанавливаем позицию вкладок вверху
        self.tab_widget.tabBar().hide()  # Полностью скрываем панель вкладок
        
        # Create tabs for each mode
        modes = ['VIDEO', 'PHOTO', 'TIMELAPSE']
        for mode in modes:
            logger.info(f"Creating tab for {mode}")
            tab = self.create_mode_tab(mode)
            self.tab_widget.addTab(tab, f"{mode} Templates")
        
        main_layout.addWidget(self.tab_widget)
        
        # Connect mode switcher signal
        self.mode_switcher.modeChanged.connect(self.on_mode_changed)
        
        # Initial refresh of template lists
        self.refresh_preset_lists()
        
        # Detect and sync camera mode
        self.detect_and_sync_prime_camera_mode()

    def load_settings_descriptions(self):
        """Load settings descriptions from JSON file"""
        try:
            with open('all_avalable_gopro10_value_settings.json', 'r') as f:
                self.settings_descriptions = json.load(f)['settings']
        except Exception as e:
            logger.error(f"Failed to load settings descriptions: {e}")
            self.settings_descriptions = {}

    def create_mode_tab(self, mode):
        """Create tab for specific mode"""
        try:
            # Create tab widget
            tab = QWidget()
            layout = QVBoxLayout()
            tab.setLayout(layout)
            
            # Create and store list widget
            list_widget = QListWidget()
            list_widget.setObjectName(f"{mode}_list")
            
            # Add test items
            list_widget.addItem(f"Test {mode} Template 1")
            list_widget.addItem(f"Test {mode} Template 2")
            list_widget.addItem(f"Test {mode} Template 3")
            
            self.list_widgets[mode] = list_widget
            logger.info(f"Created and stored list widget for {mode}: {list_widget.objectName()}")
            
            # Add to layout
            layout.addWidget(QLabel(f'Available {mode} templates:'))
            layout.addWidget(list_widget)
            
            # Connect selection signal
            list_widget.itemSelectionChanged.connect(lambda: self.on_template_selected(mode))
            
            # Control buttons
            btn_layout = QHBoxLayout()
            
            create_btn = QPushButton('Create')
            create_btn.clicked.connect(lambda: self.create_preset(mode))
            btn_layout.addWidget(create_btn)
            
            apply_btn = QPushButton('Apply')
            apply_btn.clicked.connect(lambda: self.apply_preset(mode))
            btn_layout.addWidget(apply_btn)
            
            delete_btn = QPushButton('Delete')
            delete_btn.clicked.connect(lambda: self.delete_preset(mode))
            btn_layout.addWidget(delete_btn)
            
            layout.addLayout(btn_layout)
            
            # Create settings display
            settings_display = QTextEdit()
            settings_display.setObjectName(f"{mode}_settings")
            settings_display.setReadOnly(True)
            self.settings_displays[mode] = settings_display
            logger.info(f"Created and stored settings display for {mode}: {settings_display.objectName()}")
            
            layout.addWidget(QLabel('Template settings:'))
            layout.addWidget(settings_display)
            
            # Verify widget storage
            if mode in self.list_widgets and mode in self.settings_displays:
                logger.info(f"Successfully stored widgets for {mode} tab")
                logger.info(f"List widget: {self.list_widgets[mode].objectName()}")
                logger.info(f"Settings display: {self.settings_displays[mode].objectName()}")
            else:
                logger.error(f"Failed to store widgets for {mode} tab")
            
            return tab
            
        except Exception as e:
            logger.error(f"Error creating tab for {mode}: {e}", exc_info=True)
            # Create empty tab in case of error
            tab = QWidget()
            tab.setLayout(QVBoxLayout())
            return tab

    def get_current_mode_widgets(self, mode):
        """Get widgets for current mode"""
        mode = mode.upper()  # Convert to uppercase
        return self.list_widgets.get(mode), self.settings_displays.get(mode)

    def detect_and_sync_prime_camera_mode(self):
        """Detects and synchronizes the mode of the primary camera"""
        try:
            # Get the list of cameras
            cameras = discover_gopro_devices()
            if not cameras:
                logger.warning("No cameras found")
                return

            # Find the primary camera
            prime_camera = None
            for camera in cameras:
                if is_prime_camera(camera):
                    prime_camera = camera
                    break

            if not prime_camera:
                logger.warning("Primary camera not found")
                return

            logger.info(f"Primary camera found: {prime_camera['ip']}")

            # Get the camera status
            url = f"http://{prime_camera['ip']}:8080/gopro/camera/state"
            response = requests.get(url, headers=USB_HEADERS, timeout=5)
            
            if response.status_code != 200:
                logger.error(f"Error retrieving camera status. Code: {response.status_code}")
                return

            # Get the data
            status_data = response.json()
            
            # Check the response structure
            if not isinstance(status_data, dict):
                logger.error(f"Invalid response format: {status_data}")
                return

            # Get the mode from settings.144
            settings = status_data.get('settings', {})
            if not isinstance(settings, dict):
                logger.error(f"The 'settings' field is missing or has an invalid format")
                return

            # Get the current mode from settings.144
            current_mode = settings.get('144')
            logger.info(f"Value of settings.144: {current_mode}")

            # Determine the mode based on the value of settings.144
            mode_map = {
                12: 'video',      # Video mode
                16: 'photo',      # Photo mode
                13: 'timelapse'   # Timelapse mode
            }

            if current_mode in mode_map:
                mode = mode_map[current_mode]
                logger.info(f"Camera mode determined: {current_mode} -> {mode}")
                
                # Set the mode in the switcher
                self.mode_switcher.setMode(mode, save=False)
                
                # Set the corresponding tab
                tab_index = {
                    'video': 0,
                    'photo': 1,
                    'timelapse': 2
                }[mode]
                
                # Update the interface
                self.tab_widget.setCurrentIndex(tab_index)
                self.tab_widget.repaint()
                QApplication.processEvents()
                
                logger.info(f"Mode and tab set: {mode} (tab index: {tab_index})")
            else:
                logger.warning(f"Unknown mode value: {current_mode}")
            
        except Exception as e:
            logger.error(f"Error detecting camera mode: {e}")

    def on_mode_changed(self, mode):
        """Handle mode change"""
        mode = mode.lower()
        self.tab_widget.setCurrentIndex({
            'video': 0,
            'photo': 1,
            'timelapse': 2
        }[mode])

    def refresh_preset_lists(self):
        """Refresh template lists for all modes"""
        try:
            logger.info("Starting refresh_preset_lists")
            
            # Process each mode
            for mode in ['VIDEO', 'PHOTO', 'TIMELAPSE']:
                list_widget = self.list_widgets.get(mode)
                if not list_widget:
                    logger.error(f"Could not find list widget for {mode}")
                    continue
                
                # Clear existing items
                list_widget.clear()
                
                # Get templates for this mode
                mode_lower = mode.lower()
                prefix = MODE_PREFIXES[mode_lower]
                template_pattern = f"{prefix}*.json"
                
                # Find and add templates
                template_files = list(self.templates_dir.glob(template_pattern))
                logger.info(f"Found {len(template_files)} templates for {mode}")
                
                for template_file in sorted(template_files):
                    try:
                        # Get name without prefix and extension
                        name = template_file.stem[len(prefix):]
                        
                        # Add item to list
                        list_widget.addItem(name)
                        logger.info(f"Added template {name} to {mode} list")
                    except Exception as e:
                        logger.error(f"Error adding template {template_file} to list: {e}")
                
                # Force update
                list_widget.repaint()
                QApplication.processEvents()
                
                # Debug log widget state after adding templates
                logger.info(f"After refresh - {mode} list has {list_widget.count()} items")
            
        except Exception as e:
            logger.error(f"Error in refresh_preset_lists: {e}", exc_info=True)

    def create_preset(self, mode):
        """Create new template for specific mode"""
        try:
            mode = mode.lower()  # Use lowercase for file operations
            logger.info(f"\nStarting create_preset for {mode}")
            
            # Get template name
            name, ok = QInputDialog.getText(
                self, f'New {mode} template',
                'Enter template name (use only English letters, numbers, and underscores):'
            )
            
            if not ok or not name:
                logger.info("User cancelled template creation")
                return
                
            logger.info(f"User entered name: {name}")
            
            # Validate template name
            if not all(c.isascii() and (c.isalnum() or c == '_') for c in name):
                logger.warning(f"Invalid template name: {name}")
                QMessageBox.warning(
                    self, 'Invalid Name',
                    'Please use only English letters, numbers, and underscores'
                )
                return
            
            # Add timestamp to name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            full_name = f"{name}_{timestamp}"
            logger.info(f"Full template name: {full_name}")
            
            # Get camera list
            cameras = discover_gopro_devices()
            if not cameras:
                logger.error("No cameras found")
                QMessageBox.warning(self, 'Error', 'No cameras found')
                return
            
            logger.info(f"Found {len(cameras)} cameras")
            
            # Find prime camera
            prime_camera = None
            for camera in cameras:
                if is_prime_camera(camera):
                    prime_camera = camera
                    break
            
            if not prime_camera:
                logger.error("Prime camera not found")
                QMessageBox.warning(self, 'Error', 'Prime camera not found')
                return
            
            logger.info(f"Found prime camera: {prime_camera['ip']}")
            
            # Get settings using get_camera_status with correct endpoint and headers
            url = f"http://{prime_camera['ip']}:8080/gopro/camera/state"
            response = requests.get(url, headers=USB_HEADERS, timeout=5)
            if response.status_code != 200:
                logger.error(f"Failed to get camera status. Status code: {response.status_code}")
                QMessageBox.warning(self, 'Error', 'Failed to get camera status')
                return
                
            primary_status = response.json()
            if not primary_status:
                logger.error("Failed to get camera status")
                QMessageBox.warning(self, 'Error', 'Failed to get camera status')
                return
            
            current_settings = primary_status.get('settings', {})
            if not current_settings:
                logger.error("No settings found in camera status")
                QMessageBox.warning(self, 'Error', 'No settings found')
                return
            
            logger.info(f"Got {len(current_settings)} settings from prime camera")
            
            # Load available settings
            try:
                with open('all_avalable_gopro10_value_settings.json', 'r') as f:
                    available_settings = json.load(f)
                logger.info("Loaded available settings")
            except Exception as e:
                logger.error(f"Failed to load available settings: {e}")
                available_settings = {"settings": {}}
            
            # Create template data
            template_data = {
                "metadata": {
                    "camera_ip": prime_camera['ip'],
                    "scan_date": datetime.now().isoformat(),
                    "total_valid_settings": len(current_settings)
                },
                "settings": {}
            }
            
            # Add settings with descriptions
            for setting_id, current_value in current_settings.items():
                setting_info = available_settings["settings"].get(str(setting_id), {})
                
                setting_data = {
                    "id": int(setting_id),
                    "current_value": current_value
                }
                
                if "supported_options" in setting_info:
                    setting_data["supported_options"] = setting_info["supported_options"]
                
                template_data["settings"][setting_id] = setting_data
            
            logger.info("Template data prepared")
            
            # Save template
            template_path = self.templates_dir / f"{MODE_PREFIXES[mode]}{full_name}.json"
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2)
            
            logger.info(f"Saved template to: {template_path}")
            
            # Switch to correct tab using lowercase keys
            tab_index = {'video': 0, 'photo': 1, 'timelapse': 2}[mode]
            self.tab_widget.setCurrentIndex(tab_index)
            logger.info(f"Switched to tab {tab_index}")
            
            # Refresh all lists to ensure consistency
            self.refresh_preset_lists()
            
            # Get list widget for this mode and select new template
            list_widget = self.list_widgets.get(mode.upper())  # Use UPPERCASE for widget lookup
            if list_widget:
                # Find and select the new template
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    if item.text() == full_name:
                        list_widget.setCurrentItem(item)
                        list_widget.scrollToItem(item)
                        logger.info(f"Selected new template: {full_name}")
                        break
                        
                # Force GUI update
                list_widget.repaint()
                QApplication.processEvents()
                logger.info("GUI updated")
            else:
                logger.error(f"Could not find list widget for {mode.upper()}")
            
            QMessageBox.information(self, 'Success', 'Template created successfully')
            logger.info("Template creation completed successfully")
            
        except Exception as e:
            logger.error(f"Error in create_preset: {e}", exc_info=True)
            QMessageBox.critical(self, 'Error', f'Error creating template: {str(e)}')

    def apply_preset(self, mode):
        """Apply selected preset to cameras"""
        try:
            mode = mode.upper()
            list_widget = self.list_widgets.get(mode)
            if not list_widget:
                raise ValueError(f"No list widget found for mode {mode}")
            
            selected = list_widget.currentItem()
            if not selected:
                QMessageBox.warning(self, 'Warning', 'Please select a template')
                return
            
            template_name = selected.text()
            template_path = self.templates_dir / f"{MODE_PREFIXES[mode.lower()]}{template_name}.json"
            
            if not template_path.exists():
                raise FileNotFoundError(f"Template file not found: {template_path}")
            
            # Load settings from the template
            with open(template_path, 'r') as f:
                template_data = json.load(f)
            
            # Get settings from the template
            settings = template_data.get('settings', {})
            if not settings:
                QMessageBox.warning(self, 'Error', 'No settings found in the template')
                return

            # Format settings correctly
            formatted_settings = {}
            for setting_id, setting_data in settings.items():
                if isinstance(setting_data, dict) and 'current_value' in setting_data:
                    formatted_settings[setting_id] = setting_data['current_value']

            def apply_template_settings(progress_callback):
                try:
                    # Get the list of cameras
                    cameras = discover_gopro_devices()
                    if not cameras:
                        progress_callback("log", "❌ No cameras found")
                        return False

                    # Apply settings to all cameras in parallel
                    results = CameraSettingsManager.apply_settings_sync(
                        cameras=cameras,
                        settings=formatted_settings,
                        progress_callback=progress_callback
                    )

                    # Analyze results
                    total_cameras = len(results)
                    successful_cameras = sum(1 for r in results if r.success)
                    
                    progress_callback("log", f"\nSettings application results:")
                    progress_callback("log", f"✅ Successful: {successful_cameras} out of {total_cameras} cameras")
                    
                    if successful_cameras < total_cameras:
                        failed_cameras = [r.camera_ip for r in results if not r.success]
                        progress_callback("log", f"❌ Failed to apply settings to the following cameras: {', '.join(failed_cameras)}")
                        
                        # Show detailed error information
                        for result in results:
                            if not result.success:
                                progress_callback("log", f"\nErrors for camera {result.camera_ip}:")
                                if result.error_message:
                                    progress_callback("log", f"  {result.error_message}")
                                for setting_id, success in result.settings_applied.items():
                                    if not success:
                                        progress_callback("log", f"  ❌ Setting {setting_id} not applied")

                    return successful_cameras == total_cameras

                except Exception as e:
                    progress_callback("log", f"❌ Error: {str(e)}")
                    return False

            # Create and show progress dialog
            progress = SettingsProgressDialog(
                "Applying Template",
                apply_template_settings,
                self
            )
            progress.exec_()
            
        except Exception as e:
            logger.error(f"Error applying preset: {e}", exc_info=True)
            QMessageBox.critical(self, 'Error', f'Error applying template: {str(e)}')

    def delete_preset(self, mode):
        """Delete selected template"""
        try:
            mode = mode.upper()  # Use uppercase for widget lookup
            list_widget = self.list_widgets.get(mode)
            if not list_widget:
                logger.error(f"Could not find list widget for {mode}")
                return
                
            selected = list_widget.currentItem()
            if not selected:
                QMessageBox.warning(self, 'Warning', 'Please select a template to delete')
                return
                
            template_name = selected.text()
            prefix = MODE_PREFIXES[mode.lower()]
            template_path = self.templates_dir / f"{prefix}{template_name}.json"
            
            logger.info(f"Deleting template: {template_path}")
            
            reply = QMessageBox.question(
                self,
                'Confirm Delete',
                f'Are you sure you want to delete template "{template_name}"?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    if template_path.exists():
                        template_path.unlink()
                        logger.info(f"Template deleted: {template_path}")
                        self.refresh_preset_lists()
                        QMessageBox.information(self, 'Success', 'Template deleted successfully')
                    else:
                        logger.error(f"Template file not found: {template_path}")
                        QMessageBox.warning(self, 'Error', 'Template file not found')
                except Exception as e:
                    logger.error(f"Failed to delete template: {e}")
                    QMessageBox.critical(self, 'Error', f'Failed to delete template: {str(e)}')
                    
        except Exception as e:
            logger.error(f"Error deleting preset: {e}", exc_info=True)
            QMessageBox.critical(self, 'Error', f'Error deleting template: {str(e)}')

    def on_template_selected(self, mode):
        """Handle template selection"""
        try:
            mode = mode.upper()  # Convert to uppercase
            list_widget = self.list_widgets.get(mode)
            settings_display = self.settings_displays.get(mode)
            if not list_widget or not settings_display:
                logger.error(f"Could not find widgets for {mode}")
                return
                
            selected = list_widget.currentItem()
            if not selected:
                settings_display.clear()
                return
                
            template_name = selected.text()
            template_path = self.templates_dir / f"{MODE_PREFIXES[mode.lower()]}{template_name}.json"
            
            if not template_path.exists():
                settings_display.setText("Template file not found")
                return
                
            # Load and display template settings
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                
            # Format settings display
            display_text = []
            display_text.append("Template Information:")
            display_text.append("-" * 40)
            
            # Add metadata
            metadata = template_data.get("metadata", {})
            display_text.append(f"Camera IP: {metadata.get('camera_ip', 'Unknown')}")
            display_text.append(f"Scan Date: {metadata.get('scan_date', 'Unknown')}")
            display_text.append(f"Total Settings: {len(template_data.get('settings', {}))}")
            display_text.append("")
            
            # Add settings
            display_text.append("Settings:")
            display_text.append("-" * 40)
            
            settings = template_data.get("settings", {})
            for setting_id, setting_data in settings.items():
                # Get setting description
                setting_info = self.settings_descriptions.get(str(setting_id), {})
                setting_name = setting_info.get("name", f"Setting {setting_id}")
                
                current_value = setting_data.get("current_value")
                supported_options = setting_data.get("supported_options", [])
                
                display_text.append(f"{setting_name}:")
                display_text.append(f"  Current Value: {current_value}")
                if supported_options:
                    display_text.append(f"  Supported Options: {', '.join(map(str, supported_options))}")
                display_text.append("")
            
            settings_display.setText("\n".join(display_text))
            
        except Exception as e:
            logger.error(f"Error displaying template settings: {e}", exc_info=True)
            settings_display.setText(f"Error loading template: {str(e)}")