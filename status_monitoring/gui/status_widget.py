from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QProgressBar)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPalette

class StatusWidget(QWidget):
    def __init__(self, camera_status, parent=None):
        super().__init__(parent)
        self.camera_status = camera_status
        self.setup_ui()
        self.setup_timers()
        
    def setup_ui(self):
        """Инициализация UI компонентов"""
        layout = QVBoxLayout(self)
        
        # Батарея
        battery_layout = QHBoxLayout()
        self.battery_label = QLabel("Battery:")
        self.battery_progress = QProgressBar()
        self.battery_progress.setRange(0, 100)
        self.battery_progress.setTextVisible(True)
        battery_layout.addWidget(self.battery_label)
        battery_layout.addWidget(self.battery_progress)
        layout.addLayout(battery_layout)
        
        # Хранилище
        storage_layout = QHBoxLayout()
        self.storage_label = QLabel("Storage:")
        self.storage_progress = QProgressBar()
        self.storage_progress.setRange(0, 100)
        self.storage_progress.setTextVisible(True)
        storage_layout.addWidget(self.storage_label)
        storage_layout.addWidget(self.storage_progress)
        layout.addLayout(storage_layout)
        
        # Статус записи и занятости
        status_layout = QHBoxLayout()
        self.busy_indicator = QLabel("IDLE")
        self.busy_indicator.setStyleSheet("padding: 2px; border: 1px solid gray;")
        self.recording_indicator = QLabel("NOT REC")
        self.recording_indicator.setStyleSheet("padding: 2px; border: 1px solid gray;")
        status_layout.addWidget(self.busy_indicator)
        status_layout.addWidget(self.recording_indicator)
        layout.addLayout(status_layout)
        
    def setup_timers(self):
        """Настройка таймеров обновления"""
        # Таймер для батареи - каждые 30 секунд
        self.battery_timer = QTimer(self)
        self.battery_timer.timeout.connect(self.update_battery)
        self.battery_timer.start(30000)
        
        # Таймер для хранилища - каждые 60 секунд
        self.storage_timer = QTimer(self)
        self.storage_timer.timeout.connect(self.update_storage)
        self.storage_timer.start(60000)
        
        # Таймер для статуса - каждую секунду
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)
        
        # Первоначальное обновление
        self.update_all()
        
    def update_battery(self):
        """Обновление индикатора батареи"""
        if self.camera_status.update_battery_status():
            level = self.camera_status.battery_level
            self.battery_progress.setValue(level)
            
            # Установка цвета в зависимости от уровня
            if level <= 10:
                self.battery_progress.setStyleSheet(
                    "QProgressBar::chunk { background-color: red; }"
                )
            elif level <= 20:
                self.battery_progress.setStyleSheet(
                    "QProgressBar::chunk { background-color: orange; }"
                )
            else:
                self.battery_progress.setStyleSheet(
                    "QProgressBar::chunk { background-color: green; }"
                )
                
    def update_storage(self):
        """Обновление индикатора хранилища"""
        if self.camera_status.update_state():
            # Get storage info from camera state
            state = self.camera_status.state
            used_percent = state.storage_percent_used
            self.storage_progress.setValue(used_percent)
            
            # Format storage values with 1 decimal place
            remaining_gb = state.storage_remaining_gb
            total_gb = state.storage_total_gb
            
            # Show storage in GB with 1 decimal place
            self.storage_progress.setFormat(
                f"{remaining_gb:.1f}GB / {total_gb:.1f}GB ({used_percent}% used)"
            )
            
            # Установка цвета в зависимости от свободного места
            if remaining_gb < 1:
                self.storage_progress.setStyleSheet(
                    "QProgressBar::chunk { background-color: red; }"
                )
            elif remaining_gb < 5:
                self.storage_progress.setStyleSheet(
                    "QProgressBar::chunk { background-color: orange; }"
                )
            else:
                self.storage_progress.setStyleSheet(
                    "QProgressBar::chunk { background-color: green; }"
                )
                    
    def update_status(self):
        """Обновление индикаторов состояния"""
        if self.camera_status.update_camera_state():
            # Индикатор занятости
            if self.camera_status.state.system_busy:
                self.busy_indicator.setText("BUSY")
                self.busy_indicator.setStyleSheet(
                    "background-color: yellow; color: black; padding: 2px; border: 1px solid gray;"
                )
            elif self.camera_status.state.camera_control == 2:  # EXTERNAL control
                self.busy_indicator.setText("USB")
                self.busy_indicator.setStyleSheet(
                    "background-color: blue; color: white; padding: 2px; border: 1px solid gray;"
                )
            else:
                self.busy_indicator.setText("IDLE")
                self.busy_indicator.setStyleSheet(
                    "background-color: #90EE90; color: black; padding: 2px; border: 1px solid gray;"
                )
                
            # Индикатор записи
            if self.camera_status.state.encoding_active:
                self.recording_indicator.setText("REC")
                self.recording_indicator.setStyleSheet(
                    "background-color: red; color: white; padding: 2px; border: 1px solid gray;"
                )
            else:
                self.recording_indicator.setText("NOT REC")
                self.recording_indicator.setStyleSheet(
                    "background-color: #90EE90; color: black; padding: 2px; border: 1px solid gray;"
                )
                
    def update_all(self):
        """Обновление всех индикаторов"""
        self.update_battery()
        self.update_storage()
        self.update_status() 