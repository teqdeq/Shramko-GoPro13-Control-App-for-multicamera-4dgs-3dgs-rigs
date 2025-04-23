import sys
import os
import traceback
import subprocess
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QPushButton, QLabel, QTextEdit, QFileDialog,
                             QMessageBox, QFrame, QGridLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor
from datetime import datetime
from pathlib import Path

# Initializing logging
from utils import setup_logging, get_app_root, get_data_dir, check_dependencies
from app_init import init_app

# Creating a logger for this module
logger = setup_logging('gui')

# Importing the remaining modules
from copy_progress_widget import CopyProgressWidget
from copy_manager import CopyManager
from preset_manager_gui import PresetManagerDialog
from single_photo_timelapse_gui import SinglePhotoTimelapseGUI
from power_management import PowerManager

# Modern color scheme
COLORS = {
    'primary': '#2196F3',      # Blue
    'success': '#4CAF50',      # Green
    'warning': '#FFC107',      # Yellow
    'danger': '#F44336',       # Red
    'info': '#00BCD4',         # Cyan
    'dark': '#212121',         # Dark gray
    'light': '#F5F5F5',        # Light gray
    'white': '#FFFFFF',
    'black': '#000000'
}

# Button styles
BUTTON_STYLES = {
    'primary': f"""
        QPushButton {{
            background-color: {COLORS['primary']};
            color: {COLORS['white']};
            border: none;
            border-radius: 8px;
            padding: 12px;
            font-size: 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #1976D2;
        }}
        QPushButton:pressed {{
            background-color: #0D47A1;
        }}
        QPushButton:disabled {{
            background-color: #BDBDBD;
            color: #757575;
        }}
    """,
    'success': f"""
        QPushButton {{
            background-color: {COLORS['success']};
            color: {COLORS['white']};
            border: none;
            border-radius: 8px;
            padding: 12px;
            font-size: 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #388E3C;
        }}
        QPushButton:pressed {{
            background-color: #1B5E20;
        }}
        QPushButton:disabled {{
            background-color: #BDBDBD;
            color: #757575;
        }}
    """,
    'warning': f"""
        QPushButton {{
            background-color: {COLORS['warning']};
            color: {COLORS['black']};
            border: none;
            border-radius: 8px;
            padding: 12px;
            font-size: 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #FFA000;
        }}
        QPushButton:pressed {{
            background-color: #FF6F00;
        }}
        QPushButton:disabled {{
            background-color: #BDBDBD;
            color: #757575;
        }}
    """,
    'danger': f"""
        QPushButton {{
            background-color: {COLORS['danger']};
            color: {COLORS['white']};
            border: none;
            border-radius: 8px;
            padding: 12px;
            font-size: 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #D32F2F;
        }}
        QPushButton:pressed {{
            background-color: #B71C1C;
        }}
        QPushButton:disabled {{
            background-color: #BDBDBD;
            color: #757575;
        }}
    """,
    'info': f"""
        QPushButton {{
            background-color: {COLORS['info']};
            color: {COLORS['white']};
            border: none;
            border-radius: 8px;
            padding: 12px;
            font-size: 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #0097A7;
        }}
        QPushButton:pressed {{
            background-color: #006064;
        }}
        QPushButton:disabled {{
            background-color: #BDBDBD;
            color: #757575;
        }}
    """
}

class ScriptRunner(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

    def __init__(self, script_path, additional_args=None):
        super().__init__()
        self.script_path = script_path
        self.additional_args = additional_args or []

    def run(self):
        try:
            if not os.path.isfile(self.script_path):
                raise FileNotFoundError(f"Script {self.script_path} not found.")

            self.output_signal.emit(f"Running script: {self.script_path}")
            command = ["python", self.script_path] + self.additional_args

            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
            )
            with process.stdout as stdout, process.stderr as stderr:
                for line in iter(stdout.readline, ""):
                    if line:
                        self.output_signal.emit(line.strip())
                for line in iter(stderr.readline, ""):
                    if line:
                        self.output_signal.emit(f"[ERROR] {line.strip()}")

            process.wait()
            if process.returncode == 0:
                self.output_signal.emit(f"Script {self.script_path} finished successfully.")
                self.finished_signal.emit(True)
            else:
                self.output_signal.emit(f"Script {self.script_path} finished with errors. Exit code: {process.returncode}")
                self.finished_signal.emit(False)

        except Exception as e:
            error_message = f"Error running {self.script_path}: {e}\n{traceback.format_exc()}"
            self.output_signal.emit(error_message)
            self.finished_signal.emit(False)


class KeepAliveThread(QThread):
    """Thread to send periodic keep-alive commands to cameras"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_running = True
        self.keep_alive_interval = 30  # Send keep-alive every 30 seconds
        self.log_signal = pyqtSignal(str)  # Signal for logging keep-alive status

    def run(self):
        while self.is_running:
            try:
                # Import the camera list module
                import goprolist_and_start_usb
                cameras = goprolist_and_start_usb.get_camera_list()
                
                # Send keep-alive to each camera
                for camera in cameras:
                    try:
                        # Send a simple status check command to keep the connection alive
                        camera.get_status()
                        self.log_signal.emit(f"Keep-alive sent to camera {camera.serial_number}")
                    except Exception as e:
                        self.log_signal.emit(f"Warning: Failed to send keep-alive to camera {camera.serial_number}: {str(e)}")
                
                # Sleep until next keep-alive
                for _ in range(self.keep_alive_interval):
                    if not self.is_running:
                        break
                    self.msleep(1000)  # Sleep in 1-second intervals to allow for quick stopping
                    
            except Exception as e:
                self.log_signal.emit(f"Error in keep-alive thread: {str(e)}")
                self.msleep(1000)  # Sleep briefly before retrying

    def stop(self):
        self.is_running = False

class RecordThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    error_signal = pyqtSignal(str)

    def __init__(self, is_recording, parent=None):
        super().__init__(parent)
        self.is_recording = is_recording

    def run(self):
        try:
            # Define a log handler to capture logs
            class LogHandler(logging.Handler):
                def __init__(self, signal):
                    super().__init__()
                    self.signal = signal

                def emit(self, record):
                    msg = self.format(record)
                    self.signal.emit(msg)

            logger = logging.getLogger()
            handler = LogHandler(self.progress_signal)
            handler.setFormatter(logging.Formatter('%(message)s'))
            logger.addHandler(handler)

            try:
                if not self.is_recording:  # Starting recording
                    import goprolist_usb_activate_time_sync_record
                    goprolist_usb_activate_time_sync_record.main()
                    self.progress_signal.emit("Recording started successfully")
                else:  # Stopping recording
                    import stop_record
                    stop_record.main()
                    self.progress_signal.emit("Recording stopped successfully")

                self.finished_signal.emit(True)
            except Exception as e:
                error_msg = f"Error during recording operation: {str(e)}"
                logging.error(error_msg)
                self.error_signal.emit(error_msg)
                self.finished_signal.emit(False)
            finally:
                logger.removeHandler(handler)

        except Exception as e:
            error_msg = f"Thread error: {str(e)}"
            logging.error(error_msg)
            self.error_signal.emit(error_msg)
            self.finished_signal.emit(False)


class GoProControlApp(QMainWindow):
    log_signal = pyqtSignal(str)  # Add a signal for logging messages

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shramko Andrii GoPro Control Interface")
        self.is_recording = False
        self.log_content = []
        self.download_folder = None
        self.connected_cameras_count = 0  # Initialize the camera count

        # Set window size for 7-inch touch screen
        self.setMinimumSize(800, 800)  # Increased height from 480 to 600
        self.resize(800, 800)  # Set initial size
        
        # Apply modern style
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['light']};
            }}
            QTabWidget::pane {{
                border: 1px solid {COLORS['dark']};
                background: {COLORS['white']};
            }}
            QTabBar::tab {{
                background: {COLORS['light']};
                color: {COLORS['dark']};
                padding: 8px 16px;
                border: 1px solid {COLORS['dark']};
            }}
            QTabBar::tab:selected {{
                background: {COLORS['primary']};
                color: {COLORS['white']};
            }}
            QLabel {{
                font-size: 14px;
                color: {COLORS['dark']};
            }}
            QTextEdit {{
                background-color: {COLORS['white']};
                border: 1px solid {COLORS['dark']};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
        """)

        # Getting paths to directories
        self.app_root = get_app_root()
        self.data_dir = get_data_dir()

        # Main Widget and Layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setSpacing(16)  # Increased spacing between elements
        self.layout.setContentsMargins(16, 16, 16, 16)  # Add margins

        # Tabs
        self.tab_control = QTabWidget()
        self.layout.addWidget(self.tab_control)

        self.control_tab = QWidget()
        self.download_tab = QWidget()

        self.tab_control.addTab(self.control_tab, "Control")
        self.tab_control.addTab(self.download_tab, "Download & Format")

        # Control Tab Layout
        self.control_layout = QVBoxLayout(self.control_tab)
        self.control_layout.setSpacing(16)
        self.control_layout.setContentsMargins(16, 16, 16, 16)
        self.control_layout.setStretch(0, 0)  # Don't stretch the camera count label
        self.control_layout.setStretch(1, 0)  # Don't stretch the button container
        self.control_layout.setStretch(2, 1)  # Stretch the log window
        self.control_layout.setStretch(3, 0)  # Don't stretch the save log button
        self.control_layout.setStretch(4, 0)  # Don't stretch the secondary controls

        # Camera count label with modern styling
        self.camera_count_label = QLabel("Connected Cameras: 0")
        self.camera_count_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {COLORS['primary']};
            padding: 8px;
            background-color: {COLORS['white']};
            border-radius: 8px;
        """)
        self.control_layout.addWidget(self.camera_count_label)

        # Create button container for better organization
        self.button_container = QFrame()
        self.button_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['white']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        self.button_layout = QGridLayout(self.button_container)
        self.button_layout.setSpacing(12)
        self.button_layout.setContentsMargins(8, 8, 8, 8)
        self.control_layout.addWidget(self.button_container)

        # Connect button with primary style
        self.connect_button = QPushButton("Connect to Cameras")
        self.connect_button.setFixedHeight(60)  # Increased height for touch
        self.connect_button.setStyleSheet(BUTTON_STYLES['primary'])
        self.connect_button.clicked.connect(self.connect_to_cameras)
        self.button_layout.addWidget(self.connect_button, 0, 0)  # Row 0, Column 0

        # Copy settings button with info style
        self.copy_settings_button = QPushButton("Copy Settings from Prime Camera")
        self.copy_settings_button.setFixedHeight(60)
        self.copy_settings_button.setStyleSheet(BUTTON_STYLES['info'])
        self.copy_settings_button.clicked.connect(self.copy_settings_from_prime)
        self.button_layout.addWidget(self.copy_settings_button, 0, 1)  # Row 0, Column 1

        # Record button with success/danger style
        self.record_button = QPushButton("Record")
        self.record_button.setFixedHeight(80)  # Extra large for main action
        self.record_button.setStyleSheet(BUTTON_STYLES['success'])
        self.record_button.clicked.connect(self.toggle_record)
        self.button_layout.addWidget(self.record_button, 1, 0, 1, 2)  # Row 1, spans both columns

        # Photo/Video mode buttons with primary style
        self.photo_mode_button = QPushButton("Photo Mode")
        self.photo_mode_button.setFixedHeight(60)
        self.photo_mode_button.setStyleSheet(BUTTON_STYLES['primary'])
        self.photo_mode_button.clicked.connect(lambda: self.run_script("photo_mode.py", self.photo_mode_button))
        self.button_layout.addWidget(self.photo_mode_button, 3, 0)  # Row 3, Column 0

        self.video_mode_button = QPushButton("Video Mode")
        self.video_mode_button.setFixedHeight(60)
        self.video_mode_button.setStyleSheet(BUTTON_STYLES['primary'])
        self.video_mode_button.clicked.connect(lambda: self.run_script("video_mode.py", self.video_mode_button))
        self.button_layout.addWidget(self.video_mode_button, 3, 1)  # Row 3, Column 1

        # Log Window with modern styling
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(150)  # Increased height for better visibility
        self.control_layout.addWidget(self.log_text)

        # Save Log button with info style
        self.save_log_button = QPushButton("Save Log")
        self.save_log_button.setFixedHeight(50)
        self.save_log_button.setStyleSheet(BUTTON_STYLES['info'])
        self.save_log_button.clicked.connect(self.save_log)
        self.control_layout.addWidget(self.save_log_button)

        # Secondary controls container
        self.secondary_controls_container = QFrame()
        self.secondary_controls_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['white']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        self.secondary_controls_layout = QGridLayout(self.secondary_controls_container)
        self.secondary_controls_layout.setSpacing(12)
        self.secondary_controls_layout.setContentsMargins(8, 8, 8, 8)
        self.control_layout.addWidget(self.secondary_controls_container)

        # Move these buttons to the secondary controls container
        self.set_preset_button = QPushButton("Set First Camera Preset on All Cameras")
        self.set_preset_button.setFixedHeight(60)
        self.set_preset_button.setStyleSheet(BUTTON_STYLES['info'])
        self.set_preset_button.clicked.connect(self.set_first_camera_preset)
        self.secondary_controls_layout.addWidget(self.set_preset_button, 0, 0)  # Row 0, Column 0

        self.turn_off_button = QPushButton("Turn Off Cameras")
        self.turn_off_button.setFixedHeight(60)
        self.turn_off_button.setStyleSheet(BUTTON_STYLES['warning'])
        self.turn_off_button.clicked.connect(self.turn_off_cameras)
        self.secondary_controls_layout.addWidget(self.turn_off_button, 0, 1)  # Row 0, Column 1

        self.preset_manager_btn = QPushButton("Preset Manager")
        self.preset_manager_btn.setFixedHeight(60)
        self.preset_manager_btn.setStyleSheet(BUTTON_STYLES['info'])
        self.preset_manager_btn.clicked.connect(self.show_preset_manager)
        self.secondary_controls_layout.addWidget(self.preset_manager_btn, 1, 0)  # Row 1, Column 0
        
        self.timelapse_btn = QPushButton("Single Photo Timelapse")
        self.timelapse_btn.setFixedHeight(60)
        self.timelapse_btn.setStyleSheet(BUTTON_STYLES['primary'])
        self.timelapse_btn.clicked.connect(self.show_timelapse)
        self.secondary_controls_layout.addWidget(self.timelapse_btn, 1, 1)  # Row 1, Column 1

        # Download Tab Layout
        self.download_layout = QVBoxLayout(self.download_tab)
        self.download_layout.setSpacing(16)
        self.download_layout.setContentsMargins(16, 16, 16, 16)

        # Download folder label with modern styling
        self.download_label = QLabel("No folder selected")
        self.download_label.setStyleSheet(f"""
            font-size: 16px;
            color: {COLORS['primary']};
            padding: 8px;
            background-color: {COLORS['white']};
            border-radius: 8px;
        """)
        self.download_layout.addWidget(self.download_label)

        # Download buttons container
        self.download_button_container = QFrame()
        self.download_button_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['white']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        self.download_button_layout = QGridLayout(self.download_button_container)
        self.download_button_layout.setSpacing(12)
        self.download_button_layout.setContentsMargins(8, 8, 8, 8)
        self.download_layout.addWidget(self.download_button_container)

        # Download buttons with modern styling
        self.select_folder_button = QPushButton("Select Download Folder")
        self.select_folder_button.setFixedHeight(60)
        self.select_folder_button.setStyleSheet(BUTTON_STYLES['primary'])
        self.select_folder_button.clicked.connect(self.select_download_folder)
        self.download_button_layout.addWidget(self.select_folder_button, 0, 0, 1, 2)  # Spans both columns

        self.download_button = QPushButton("Download all files from all Cameras")
        self.download_button.setFixedHeight(60)
        self.download_button.setStyleSheet(BUTTON_STYLES['success'])
        self.download_button.clicked.connect(self.download_files)
        self.download_button_layout.addWidget(self.download_button, 1, 0)  # Row 1, Column 0

        self.format_button = QPushButton("Format All Cameras")
        self.format_button.setFixedHeight(60)
        self.format_button.setStyleSheet(BUTTON_STYLES['danger'])
        self.format_button.clicked.connect(self.format_all_cameras)
        self.download_button_layout.addWidget(self.format_button, 1, 1)  # Row 1, Column 1

        # Download log with modern styling
        self.download_log_text = QTextEdit()
        self.download_log_text.setReadOnly(True)
        self.download_log_text.setMinimumHeight(100)
        self.download_layout.addWidget(self.download_log_text)

        # Initialize the copy progress widget
        self.init_copy_progress()
        
        self.power_manager = PowerManager()
        
        self.log_signal.connect(self.append_log_message)

    def init_copy_progress(self):
        """Initializing the copy progress widget"""
        self.copy_progress = CopyProgressWidget()
        self.download_layout.addWidget(self.copy_progress)
        
        # Creating a copy manager
        self.copy_manager = CopyManager()
        
        # Connecting progress update signals
        self.copy_manager.progress_signal.connect(
            self.copy_progress.update_signal.emit
        )
        self.copy_manager.error_signal.connect(
            lambda msg: self.log_message(f"Error: {msg}")
        )
        self.copy_manager.status_signal.connect(
            self.copy_progress.update_signal.emit
        )
        
        # Connecting management signals
        self.copy_progress.pause_signal.connect(self.copy_manager.pause)
        self.copy_progress.resume_signal.connect(self.copy_manager.resume)
        self.copy_progress.cancel_signal.connect(self.copy_manager.cancel)
        
        # Setting the stretch policy for the progress widget
        self.download_layout.setStretchFactor(self.copy_progress, 1)
        
    def log_message(self, message):
        self.log_signal.emit(message)  # Emit the signal instead of directly updating the GUI

    def append_log_message(self, message):
        """Slot to append log messages to the GUI"""
        self.log_content.append(message)
        self.log_text.append(message)
        self.download_log_text.append(message)

    def run_script(self, script_name, button_to_enable, additional_args=None):
        # Disable the button and update its text immediately
        button_to_enable.setEnabled(False)
        if button_to_enable == self.photo_mode_button or button_to_enable == self.video_mode_button:
            button_to_enable.setText(f"{button_to_enable.text()} (Processing...)")
            self.log_message(f"Starting {button_to_enable.text()} operation...")
            # Force the UI to update immediately
            QApplication.processEvents()

        try:
            script_path = self.app_root / script_name
            if not script_path.exists():
                raise FileNotFoundError(f"Script {script_name} not found at {script_path}")

            command = [sys.executable, str(script_path)]
            if additional_args:
                command.extend(additional_args)

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            with process.stdout as stdout, process.stderr as stderr:
                for line in iter(stdout.readline, ""):
                    if line:
                        # Remove [ERROR] prefix if it's not actually an error
                        line = line.replace("[ERROR] ", "") if "successfully" in line else line
                        self.log_message(line.strip())
                for line in iter(stderr.readline, ""):
                    if line:
                        self.log_message(f"[ERROR] {line.strip()}")

            process.wait()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, command)

            # Only re-enable the button if the operation was successful
            if button_to_enable == self.photo_mode_button or button_to_enable == self.video_mode_button:
                self.log_message(f"{button_to_enable.text()} operation completed successfully")
                # Keep the button disabled for a moment to show completion
                QTimer.singleShot(1000, lambda: self.enable_button(button_to_enable))

        except FileNotFoundError as e:
            logging.error(f"File not found: {e}")
            self.log_message(f"Error: {str(e)}")
            self.enable_button(button_to_enable)
        except subprocess.CalledProcessError as e:
            logging.error(f"Script {script_name} failed with exit code {e.returncode}")
            self.log_message(f"Error: Script {script_name} failed with exit code {e.returncode}. Command: {e.cmd}")
            self.enable_button(button_to_enable)
        except Exception as e:
            logging.error(f"Error running script {script_name}: {e}")
            self.log_message(f"Error: {str(e)}")
            self.enable_button(button_to_enable)

    def enable_button(self, button):
        """Helper method to safely enable a button and restore its text"""
        button.setEnabled(True)
        if button == self.photo_mode_button:
            button.setText("Photo Mode")
        elif button == self.video_mode_button:
            button.setText("Video Mode")
        elif button == self.record_button:
            if self.is_recording:
                button.setText("Stop")
            else:
                button.setText("Record")

    def on_script_finished(self, success, button_to_enable):
        if not success:
            QMessageBox.critical(self, "Script Error", "The script did not complete successfully.")
            self.enable_button(button_to_enable)

    def connect_to_cameras(self):
        self.connect_button.setEnabled(False)
        
        class ConnectThread(QThread):
            progress_signal = pyqtSignal(str)
            finished_signal = pyqtSignal(bool)
            
            def run(self):
                try:
                    # Capturing logs for display in GUI
                    class LogHandler(logging.Handler):
                        def __init__(self, signal):
                            super().__init__()
                            self.signal = signal
                            
                        def emit(self, record):
                            msg = self.format(record)
                            self.signal.emit(msg)
                    
                    # Adding a handler to capture logs
                    logger = logging.getLogger()
                    handler = LogHandler(self.progress_signal)
                    handler.setFormatter(logging.Formatter('%(message)s'))
                    logger.addHandler(handler)
                    
                    try:
                        # Connect to the cameras
                        import goprolist_and_start_usb
                        goprolist_and_start_usb.main()
                        self.finished_signal.emit(True)
                    except Exception as e:
                        logging.error(f"Error connecting to cameras: {e}")
                        self.progress_signal.emit(f"Error: {str(e)}")
                        self.finished_signal.emit(False)
                    finally:
                        logger.removeHandler(handler)
                        
                except Exception as e:
                    logging.error(f"Thread error: {e}")
                    self.progress_signal.emit(f"Thread error: {str(e)}")
                    self.finished_signal.emit(False)
        
        # Create and launch the stream
        self.connect_thread = ConnectThread()
        self.connect_thread.progress_signal.connect(self.log_message)
        self.connect_thread.finished_signal.connect(
            lambda success: self.on_connect_finished(success)
        )
        self.connect_thread.start()
    
    def on_connect_finished(self, success):
        """Handler for ending the connection to the cameras"""
        self.connect_button.setEnabled(True)
        if success:
            # Update the connected cameras count
            self.connected_cameras_count = self.get_connected_cameras_count()
            logger.info(f"Connected cameras count: {self.connected_cameras_count}")
            self.camera_count_label.setText(f"Connected Cameras: {self.connected_cameras_count}")
            self.camera_count_label.repaint()  # Force UI update
            self.log_message("Successfully connected to cameras")
        else:
            self.log_message("Failed to connect to cameras")
            QMessageBox.critical(
                self,
                "Error",
                "Failed to connect to cameras"
            )

    def get_connected_cameras_count(self):
        """Retrieve the number of connected cameras"""
        try:
            # Replace this with the actual logic to count connected cameras
            import goprolist_and_start_usb
            count = goprolist_and_start_usb.get_camera_count()
            logger.info(f"Retrieved camera count: {count}")
            return count
        except Exception as e:
            logging.error(f"Error retrieving camera count: {e}")
            return 0

    def copy_settings_from_prime(self):
        """Copies settings from the main camera to the others while displaying progress"""
        try:
            # Import and create progress dialog
            from progress_dialog import SettingsProgressDialog
            from read_and_write_all_settings_from_prime_to_other_v02 import copy_camera_settings_sync
            
            dialog = SettingsProgressDialog(
                "Copying settings from the main camera",
                copy_camera_settings_sync,
                self
            )
            dialog.exec_()
            
        except Exception as e:
            logging.error(f"Error copying settings: {e}")
            QMessageBox.critical(
                self,
                'Error',
                f'Error while copying settings: {str(e)}'
            )

    def toggle_record(self):
        """Modified toggle_record method in GoProControlApp class"""
        try:
            # Disable the button immediately
            self.record_button.setEnabled(False)
            
            # Create and start the RecordThread with current recording state
            self.record_thread = RecordThread(self.is_recording, self)
            self.record_thread.progress_signal.connect(self.log_message)
            self.record_thread.error_signal.connect(self.handle_record_error)
            self.record_thread.finished_signal.connect(self.on_record_finished)
            self.record_thread.start()

            # Update button appearance based on current state
            if self.is_recording:  # Currently recording, about to stop
                self.record_button.setStyleSheet(BUTTON_STYLES['success'])
                self.record_button.setText("Record")
            else:  # Not recording, about to start
                self.record_button.setStyleSheet(BUTTON_STYLES['danger'])
                self.record_button.setText("Stop Recording")

        except Exception as e:
            self.log_message(f"Error in toggle_record: {str(e)}")
            self.record_button.setEnabled(True)
            self.record_button.setStyleSheet(BUTTON_STYLES['success'])
            self.record_button.setText("Record")

    def handle_record_error(self, error_msg):
        """Handler for recording errors"""
        self.log_message(f"Recording error: {error_msg}")
        QMessageBox.critical(
            self,
            "Recording Error",
            f"An error occurred during recording:\n{error_msg}"
        )
        # Reset button state
        self.record_button.setEnabled(True)
        self.record_button.setStyleSheet(BUTTON_STYLES['success'])
        self.record_button.setText("Record")
        self.is_recording = False

    def on_record_finished(self, success):
        """Handler for ending the recording operation"""
        if success:
            # Only toggle recording state if operation was successful
            self.is_recording = not self.is_recording
            if self.is_recording:
                self.record_button.setStyleSheet(BUTTON_STYLES['danger'])
                self.record_button.setText("Stop Recording")
            else:
                self.record_button.setStyleSheet(BUTTON_STYLES['success'])
                self.record_button.setText("Record")
            self.log_message("Recording operation completed successfully")
        else:
            # Reset to non-recording state on failure
            self.is_recording = False
            self.record_button.setStyleSheet(BUTTON_STYLES['success'])
            self.record_button.setText("Record")
            self.log_message("Recording operation failed")
            QMessageBox.critical(
                self,
                "Error",
                "Failed to complete recording operation"
            )
        
        # Always re-enable the button
        self.record_button.setEnabled(True)

    def set_first_camera_preset(self):
        self.set_preset_button.setEnabled(False)
        
        class PresetThread(QThread):
            progress_signal = pyqtSignal(str)
            finished_signal = pyqtSignal(bool)
            
            def run(self):
                try:
                    # Intercept logs for display in the GUI
                    class LogHandler(logging.Handler):
                        def __init__(self, signal):
                            super().__init__()
                            self.signal = signal
                            
                        def emit(self, record):
                            msg = self.format(record)
                            self.signal.emit(msg)
                    
                    # Add a handler for intercepting logs
                    logger = logging.getLogger()
                    handler = LogHandler(self.progress_signal)
                    handler.setFormatter(logging.Formatter('%(message)s'))
                    logger.addHandler(handler)
                    
                    try:
                        # Set the preset
                        import set_preset_0
                        set_preset_0.main()
                        self.finished_signal.emit(True)
                    except Exception as e:
                        logging.error(f"Error setting preset: {e}")
                        self.progress_signal.emit(f"Error: {str(e)}")
                        self.finished_signal.emit(False)
                    finally:
                        logger.removeHandler(handler)
                        
                except Exception as e:
                    logging.error(f"Thread error: {e}")
                    self.progress_signal.emit(f"Thread error: {str(e)}")
                    self.finished_signal.emit(False)
        
        # Create and start the stream
        self.preset_thread = PresetThread()
        self.preset_thread.progress_signal.connect(self.log_message)
        self.preset_thread.finished_signal.connect(
            lambda success: self.on_preset_finished(success)
        )
        self.preset_thread.start()
    
    def on_preset_finished(self, success):
        """Handler for ending the preset installation"""
        self.set_preset_button.setEnabled(True)
        if success:
            self.log_message("Preset set successfully")
        else:
            self.log_message("Failed to set preset")
            QMessageBox.critical(
                self,
                "Error",
                "Failed to set camera preset"
            )

    def save_log(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"gopro_control_log_{timestamp}.txt"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Log",
                str(self.data_dir / default_filename),
                "Text Files (*.txt)"
            )
            if file_path:
                with open(file_path, "w", encoding='utf-8') as log_file:
                    log_file.write("\n".join(self.log_content))
                logging.info(f"Log saved to {file_path}")
                self.log_message(f"Log saved to {file_path}")
        except Exception as e:
            logging.error(f"Error saving log: {e}")
            self.log_message(f"Error saving log: {e}")

    def select_download_folder(self):
        # Get the last used directory from the config
        initial_dir = self.copy_manager.config.get("last_target_dir", str(Path.home()))
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", initial_dir)
        if folder:
            self.download_folder = folder
            self.download_label.setText(f"Selected folder: {self.download_folder}")
            self.download_label.setStyleSheet("color: green;")
            self.log_message(f"Selected download folder: {self.download_folder}")

    def download_files(self):
        """Handler for the download button click"""
        try:
            with self.power_manager.prevent_system_sleep():
                # Clear previous progress
                self.copy_progress.clear()
                
                # If no folder is selected, prompt for it
                if not self.download_folder:
                    # Get the last used directory from the config
                    initial_dir = self.copy_manager.config.get("last_target_dir", str(Path.home()))
                    target_dir = QFileDialog.getExistingDirectory(
                        self,
                        "Select Directory for Download",
                        initial_dir
                    )
                    if not target_dir:
                        return
                    self.download_folder = target_dir
                    self.download_label.setText(f"Selected folder: {self.download_folder}")
                    self.download_label.setStyleSheet("color: green;")
                
                # Start copying
                self.copy_manager.start_copy_session(Path(self.download_folder))
                
        except Exception as e:
            logging.error(f"Error starting copy: {e}")
            self.log_message(f"Ошибка: {str(e)}")

    def format_all_cameras(self):
        reply = QMessageBox.question(self, "Format SD Cards", "Format all cameras? This action cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.format_button.setEnabled(False)
            self.run_script("format_sd.py", self.format_button)

    def turn_off_cameras(self):
        self.turn_off_button.setEnabled(False)
        self.run_script("Turn_Off_Cameras.py", self.turn_off_button)

    def show_preset_manager(self):
        """Shows a dialog for managing presets"""
        dialog = PresetManagerDialog(self)
        # Ensure mode detection happens before showing
        dialog.detect_and_sync_prime_camera_mode()
        dialog.show()

    def show_timelapse(self):
        """Displays the Single Photo Timelapse window"""
        self.timelapse_window = SinglePhotoTimelapseGUI()
        self.timelapse_window.show()


def main():
    try:
        # Initialize the application
        if not init_app():
            raise RuntimeError("Failed to initialize application")
             
        # Create and display the main window
        app = QApplication(sys.argv)
        window = GoProControlApp()
        window.show()
        
        # Start the main loop
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error starting application")
        msg.setInformativeText(str(e))
        msg.setWindowTitle("Error")
        msg.exec_()
        sys.exit(1)


if __name__ == "__main__":
    main()
