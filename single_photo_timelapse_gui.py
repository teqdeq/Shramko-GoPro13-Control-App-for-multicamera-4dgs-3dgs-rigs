import sys
import os
import logging
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget,
                            QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                            QSpinBox, QMessageBox, QProgressBar, QTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor

# Initialize logging
from utils import setup_logging, get_data_dir

# Create logger for this module
logger = setup_logging('timelapse_gui')

class TimelapseThread(QThread):
    progress_signal = pyqtSignal(str)
    photo_taken_signal = pyqtSignal(int)  # Emits current photo count
    time_update_signal = pyqtSignal(int)  # Emits milliseconds until next photo
    camera_status_signal = pyqtSignal(list)  # Emits list of failed cameras
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, interval_ms, total_photos=None, parent=None):
        super().__init__(parent)
        self.interval_ms = interval_ms
        self.total_photos = total_photos
        self.is_running = False
        self.photo_count = 0
        self.disabled_cameras = {}  # IP -> Thread для камер на переподключении
        
    def reconnect_camera(self, camera_ip, camera_name):
        """Поток для переподключения камеры"""
        logger.info(f"Starting reconnection thread for camera {camera_name} ({camera_ip})")
        while self.is_running:
            try:
                import start_usb
                logger.info(f"Attempting to reconnect camera {camera_name} ({camera_ip})")
                if start_usb.main(camera_ip):
                    logger.info(f"Successfully reconnected camera {camera_name}")
                    self.disabled_cameras.pop(camera_ip, None)
                    return
                else:
                    logger.warning(f"Failed to reconnect camera {camera_name}, retrying in 6 seconds...")
                    time.sleep(6)
            except Exception as e:
                logger.error(f"Error reconnecting camera {camera_name}: {str(e)}")
                time.sleep(6)
        
    def run(self):
        try:
            self.is_running = True
            
            # Setup logging handler for GUI updates
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
                # First, enable USB control on all cameras
                import goprolist_and_start_usb
                self.progress_signal.emit("Enabling USB control on cameras...")
                if not goprolist_and_start_usb.main():
                    raise Exception("Failed to enable USB control on cameras")
                self.progress_signal.emit("USB control enabled successfully")

                # Then set all cameras to photo mode
                import photo_mode
                self.progress_signal.emit("Setting cameras to photo mode...")
                if not photo_mode.main():
                    raise Exception("Failed to set cameras to photo mode")
                self.progress_signal.emit("All cameras set to photo mode successfully")
                
                next_photo_time = time.time()  # Время следующего фото
                
                while self.is_running:
                    try:
                        current_time = time.time()
                        if current_time >= next_photo_time:
                            # Take photos
                            import take_single_photo
                            start_time = time.time()

                            # Получаем список активных камер (исключая те, что на переподключении)
                            active_devices = [dev for dev in take_single_photo.get_cached_devices() 
                                             if dev['ip'] not in self.disabled_cameras]

                            if active_devices:
                                success, failed_cameras = take_single_photo.main(active_devices)
                            else:
                                success = False
                                failed_cameras = []

                            # Проверяем таймауты и запускаем переподключение
                            for cam in failed_cameras:
                                if "Timeout" in cam['error'] or "Failed to take photo" in cam['error']:
                                    camera_ip = next(device['ip'] for device in take_single_photo.get_cached_devices() 
                                                    if device['name'] == cam['name'])
                                    
                                    # Если камера еще не на переподключении
                                    if camera_ip not in self.disabled_cameras:
                                        logger.info(f"Starting USB reconnection for camera {cam['name']}")
                                        thread = Thread(target=self.reconnect_camera, 
                                                      args=(camera_ip, cam['name']))
                                        thread.daemon = True
                                        thread.start()
                                        self.disabled_cameras[camera_ip] = thread
                            
                            # Отправляем статус камер в GUI
                            self.camera_status_signal.emit(failed_cameras)
                            
                            # Увеличиваем счетчик только если хотя бы одна камера работает
                            if active_devices:
                                self.photo_count += 1
                                self.photo_taken_signal.emit(self.photo_count)

                            if failed_cameras:
                                self.progress_signal.emit(
                                    f"Photo {self.photo_count} captured with {len(failed_cameras)} problematic cameras"
                                )
                            else:
                                self.progress_signal.emit(f"Photo {self.photo_count} captured successfully on all cameras")
                            
                            # Check if we've reached total photos
                            if self.total_photos and self.photo_count >= self.total_photos:
                                self.progress_signal.emit("Completed all photos")
                                break
                            
                            # Вычисляем время следующего фото с учетом времени выполнения
                            next_photo_time = start_time + (self.interval_ms / 1000.0)
                            
                            # Если следующее время фото уже прошло из-за долгого выполнения,
                            # сразу делаем следующее фото
                            if next_photo_time <= time.time():
                                continue
                            
                        # Вычисляем оставшееся время до следующего фото
                        remaining_ms = int((next_photo_time - time.time()) * 1000)
                        if remaining_ms > 0:
                            self.time_update_signal.emit(remaining_ms)
                            # Спим короткими интервалами для возможности остановки
                            time.sleep(min(0.01, remaining_ms / 1000.0))  # Уменьшаем до 10мс
                            
                    except Exception as e:
                        logging.error(f"Error capturing photo: {e}")
                        self.progress_signal.emit(f"Error: {str(e)}")
                        self.is_running = False
                        
            finally:
                logger.removeHandler(handler)
                # Останавливаем все потоки переподключения
                self.is_running = False
                for thread in self.disabled_cameras.values():
                    thread.join(timeout=1)
                
        except Exception as e:
            logging.error(f"Thread error: {e}")
            self.progress_signal.emit(f"Thread error: {str(e)}")
            self.is_running = False
        
        self.finished_signal.emit(True)
    
    def stop(self):
        self.is_running = False


class SinglePhotoTimelapseGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Single Photo Timelapse Control")
        self.is_timelapse_running = False
        self.timelapse_thread = None
        self.settings_file = Path(get_data_dir()) / 'timelapse_settings.json'
        
        # Main Widget and Layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)
        
        # Interval input
        interval_layout = QHBoxLayout()
        self.interval_label = QLabel("Interval (milliseconds):")
        interval_layout.addWidget(self.interval_label)
        
        self.interval_input = QSpinBox()
        self.interval_input.setRange(100, 3600000)  # From 0.1 sec to 1 hour
        self.interval_input.setValue(1000)  # Default 1 second
        self.interval_input.setSingleStep(100)
        interval_layout.addWidget(self.interval_input)
        self.layout.addLayout(interval_layout)
        
        # Total photos input
        total_photos_layout = QHBoxLayout()
        self.total_photos_label = QLabel("Total photos (0 for unlimited):")
        total_photos_layout.addWidget(self.total_photos_label)
        
        self.total_photos_input = QSpinBox()
        self.total_photos_input.setRange(0, 999999)  # 0 means unlimited
        self.total_photos_input.setValue(0)
        total_photos_layout.addWidget(self.total_photos_input)
        self.layout.addLayout(total_photos_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Photo %v of %m")
        self.layout.addWidget(self.progress_bar)
        
        # Photo counter
        self.counter_label = QLabel("Photos taken: 0")
        self.layout.addWidget(self.counter_label)
        
        # Next photo timer
        self.timer_label = QLabel("Next photo in: --:--")
        self.layout.addWidget(self.timer_label)
        
        # Camera status area
        self.camera_status = QTextEdit()
        self.camera_status.setReadOnly(True)
        self.camera_status.setMaximumHeight(100)
        self.camera_status.setPlaceholderText("All cameras working normally")
        self.layout.addWidget(self.camera_status)
        
        # Control button
        self.timelapse_button = QPushButton("Start Single Photo Timelapse")
        self.timelapse_button.clicked.connect(self.toggle_timelapse)
        self.layout.addWidget(self.timelapse_button)
        
        # Status label
        self.status_label = QLabel("Status: Ready")
        self.layout.addWidget(self.status_label)
        
        # Load saved settings
        self.load_settings()
        
        # Set window size
        self.setFixedSize(400, 400)
    
    def load_settings(self):
        """Load saved settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.interval_input.setValue(settings.get('interval', 1000))
                    self.total_photos_input.setValue(settings.get('total_photos', 0))
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            settings = {
                'interval': self.interval_input.value(),
                'total_photos': self.total_photos_input.value()
            }
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    def update_camera_status(self, failed_cameras):
        """Update the camera status display"""
        if not failed_cameras:
            self.camera_status.setStyleSheet("background-color: #e8f5e9;")  # Light green
            self.camera_status.setText("All cameras working normally")
            return
            
        self.camera_status.setStyleSheet("background-color: #ffebee;")  # Light red
        status_text = "Problems detected with cameras:\n"
        for cam in failed_cameras:
            status_text += f"• {cam['name']}: {cam['error']}\n"
        self.camera_status.setText(status_text)
    
    def toggle_timelapse(self):
        if not self.is_timelapse_running:
            interval = self.interval_input.value()
            total_photos = self.total_photos_input.value()
            
            # Save settings
            self.save_settings()
            
            # Reset progress
            self.progress_bar.setValue(0)
            if total_photos > 0:
                self.progress_bar.setMaximum(total_photos)
            else:
                self.progress_bar.setMaximum(0)  # Infinite progress
            
            # Prevent system sleep
            import power_management
            power_management.prevent_sleep()
            
            # Create and start timelapse thread
            self.timelapse_thread = TimelapseThread(interval, total_photos)
            self.timelapse_thread.progress_signal.connect(self.update_status)
            self.timelapse_thread.photo_taken_signal.connect(self.update_counter)
            self.timelapse_thread.time_update_signal.connect(self.update_timer)
            self.timelapse_thread.camera_status_signal.connect(self.update_camera_status)
            self.timelapse_thread.finished_signal.connect(self.on_timelapse_finished)
            
            self.timelapse_thread.start()
            self.is_timelapse_running = True
            self.timelapse_button.setText("Stop Single Photo Timelapse")
            self.interval_input.setEnabled(False)
            self.total_photos_input.setEnabled(False)
            self.status_label.setText("Status: Running single photo timelapse...")
            
        else:
            if self.timelapse_thread:
                self.timelapse_thread.stop()
                self.timelapse_thread.wait()
                self.timelapse_thread = None
            
            # Allow system sleep
            import power_management
            power_management.allow_sleep()
            
            self.is_timelapse_running = False
            self.timelapse_button.setText("Start Single Photo Timelapse")
            self.interval_input.setEnabled(True)
            self.total_photos_input.setEnabled(True)
            self.status_label.setText("Status: Stopped")
            self.timer_label.setText("Next photo in: --:--")
            self.camera_status.setStyleSheet("")
            self.camera_status.clear()
    
    def update_status(self, message):
        self.status_label.setText(f"Status: {message}")
    
    def update_counter(self, count):
        self.counter_label.setText(f"Photos taken: {count}")
        self.progress_bar.setValue(count)
    
    def update_timer(self, remaining_ms):
        time_str = str(timedelta(milliseconds=remaining_ms))[:-3]  # Remove microseconds
        self.timer_label.setText(f"Next photo in: {time_str}")
    
    def on_timelapse_finished(self, success):
        self.is_timelapse_running = False
        self.timelapse_button.setText("Start Single Photo Timelapse")
        self.interval_input.setEnabled(True)
        self.total_photos_input.setEnabled(True)
        self.timer_label.setText("Next photo in: --:--")
        self.camera_status.setStyleSheet("")
        self.camera_status.clear()
        
        # Allow system sleep
        import power_management
        power_management.allow_sleep()
        
        if not success:
            QMessageBox.critical(
                self,
                "Error",
                "Single photo timelapse operation failed"
            )


def main():
    try:
        app = QApplication(sys.argv)
        window = SinglePhotoTimelapseGUI()
        window.show()
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