import sys
import os
import traceback
import subprocess
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QPushButton, QLabel, QTextEdit, QFileDialog,
                             QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
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


class RecordThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

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
                if self.is_recording:
                    import stop_record
                    stop_record.main()
                else:
                    import goprolist_usb_activate_time_sync_record
                    goprolist_usb_activate_time_sync_record.main()

                self.finished_signal.emit(True)
            except Exception as e:
                logging.error(f"Error during recording operation: {e}")
                self.progress_signal.emit(f"Error: {str(e)}")
                self.finished_signal.emit(False)
            finally:
                logger.removeHandler(handler)
        except Exception as e:
            logging.error(f"Thread error: {e}")
            self.progress_signal.emit(f"Thread error: {str(e)}")
            self.finished_signal.emit(False)


class GoProControlApp(QMainWindow):
    log_signal = pyqtSignal(str)  # Add a signal for logging messages

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shramko Andrii GoPro Control Interface")
        self.is_recording = False
        self.log_content = []
        self.download_folder = None
        
        # Getting paths to directories
        self.app_root = get_app_root()
        self.data_dir = get_data_dir()
        
        # Main Widget and Layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # Tabs
        self.tab_control = QTabWidget()
        self.layout.addWidget(self.tab_control)

        self.control_tab = QWidget()
        self.download_tab = QWidget()

        self.tab_control.addTab(self.control_tab, "Control")
        self.tab_control.addTab(self.download_tab, "Download & Format")

        # Control Tab Layout
        self.control_layout = QVBoxLayout(self.control_tab)
        self.connect_button = QPushButton("Connect to Cameras")
        self.connect_button.setFixedHeight(50)  # Increasing the height by 2 times
        self.connect_button.clicked.connect(self.connect_to_cameras)
        self.control_layout.addWidget(self.connect_button)

        self.copy_settings_button = QPushButton("Copy Settings from Prime Camera")
        self.copy_settings_button.setFixedHeight(50)  # Increasing the height by 2 times
        self.copy_settings_button.clicked.connect(self.copy_settings_from_prime)
        self.control_layout.addWidget(self.copy_settings_button)

        self.record_button = QPushButton("Record")
        self.record_button.setFixedHeight(75)  # Increasing the height by 3 times
        self.record_button.clicked.connect(self.toggle_record)
        self.control_layout.addWidget(self.record_button)

        self.set_preset_button = QPushButton("Set First Camera Preset on All Cameras")
        self.set_preset_button.clicked.connect(self.set_first_camera_preset)
        self.control_layout.addWidget(self.set_preset_button)

        self.turn_off_button = QPushButton("Turn Off Cameras")
        self.turn_off_button.clicked.connect(self.turn_off_cameras)
        self.control_layout.addWidget(self.turn_off_button)

        # Add Photo Mode button
        self.photo_mode_button = QPushButton("Photo Mode")
        self.photo_mode_button.setFixedHeight(50)  # Set button height
        self.photo_mode_button.clicked.connect(lambda: self.run_script("photo_mode.py", self.photo_mode_button))
        self.control_layout.addWidget(self.photo_mode_button)

        # Add Video Mode button
        self.video_mode_button = QPushButton("Video Mode")
        self.video_mode_button.setFixedHeight(50)  # Set button height
        self.video_mode_button.clicked.connect(lambda: self.run_script("video_mode.py", self.video_mode_button))
        self.control_layout.addWidget(self.video_mode_button)

        # Log Window (Control Tab)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.control_layout.addWidget(self.log_text)

        # Save Log Button
        self.save_log_button = QPushButton("Save Log")
        self.save_log_button.clicked.connect(self.save_log)
        self.control_layout.addWidget(self.save_log_button)

        # Download Tab Layout
        self.download_layout = QVBoxLayout(self.download_tab)

        self.download_label = QLabel("No folder selected")
        self.download_label.setStyleSheet("color: blue;")
        self.download_layout.addWidget(self.download_label)

        self.select_folder_button = QPushButton("Select Download Folder")
        self.select_folder_button.clicked.connect(self.select_download_folder)
        self.download_layout.addWidget(self.select_folder_button)

        self.download_button = QPushButton("Download all files from all Cameras")
        self.download_button.clicked.connect(self.download_files)
        self.download_layout.addWidget(self.download_button)

        self.format_button = QPushButton("Format All Cameras")
        self.format_button.clicked.connect(self.format_all_cameras)
        self.download_layout.addWidget(self.format_button)

        # Log Window (Download Tab)
        self.download_log_text = QTextEdit()
        self.download_log_text.setReadOnly(True)
        self.download_log_text.setMaximumHeight(100)  # Limiting the height to approximately 5 lines
        self.download_layout.addWidget(self.download_log_text)

        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Initializing the copy progress widget
        self.init_copy_progress()
        
        # Adding a preset management button to control_layout
        self.preset_manager_btn = QPushButton("Preset Manager")
    
        self.preset_manager_btn.clicked.connect(self.show_preset_manager)
        self.control_layout.addWidget(self.preset_manager_btn)
        
        # Adding a Single Photo Timelapse button to control_layout
        self.timelapse_btn = QPushButton("Single Photo Timelapse")
        self.timelapse_btn.clicked.connect(self.show_timelapse)
        self.control_layout.addWidget(self.timelapse_btn)
        
        self.power_manager = PowerManager()
        
        self.log_signal.connect(self.append_log_message)  # Connect the signal to a slot

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
                        self.log_message(line.strip())
                for line in iter(stderr.readline, ""):
                    if line:
                        self.log_message(f"[ERROR] {line.strip()}")

            process.wait()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, command)

        except FileNotFoundError as e:
            logging.error(f"File not found: {e}")
            self.log_message(f"Error: {str(e)}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Script {script_name} failed with exit code {e.returncode}")
            self.log_message(f"Error: Script {script_name} failed with exit code {e.returncode}. Command: {e.cmd}")
        except Exception as e:
            logging.error(f"Error running script {script_name}: {e}")
            self.log_message(f"Error: {str(e)}")
        finally:
            button_to_enable.setEnabled(True)

    def on_script_finished(self, success, button_to_enable):
        button_to_enable.setEnabled(True)
        if button_to_enable == self.record_button:
            if self.is_recording:
                self.record_button.setText("Stop")
            else:
                self.record_button.setText("Record")
        if not success:
            QMessageBox.critical(self, "Script Error", "The script did not complete successfully.")

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
            self.log_message("Successfully connected to cameras")
        else:
            self.log_message("Failed to connect to cameras")
            QMessageBox.critical(
                self,
                "Error",
                "Failed to connect to cameras"
            )

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
        self.record_button.setEnabled(False)

        # Create and start the RecordThread
        self.record_thread = RecordThread(self.is_recording)
        self.record_thread.progress_signal.connect(self.log_message)
        self.record_thread.finished_signal.connect(
            lambda success: self.on_record_finished(success)
        )
        self.record_thread.start()
    
    def on_record_finished(self, success):
        """Handler for ending the recording operation"""
        self.record_button.setEnabled(True)  # Ensure the button is re-enabled
        if success:
            self.is_recording = not self.is_recording
            self.record_button.setText("Stop Recording" if self.is_recording else "Record")
            self.log_message("Recording operation completed successfully")
        else:
            self.log_message("Recording operation failed")
            QMessageBox.critical(
                self,
                "Error",
                "Failed to complete recording operation"
            )

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
