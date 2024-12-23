from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QMessageBox, QInputDialog, QLabel,
    QFrame
)
from PyQt5.QtCore import Qt
from camera_presets import PresetManager
import logging
from utils import setup_logging
from goprolist_and_start_usb import discover_gopro_devices, main as connect_cameras
from progress_dialog import SettingsProgressDialog
from mode_switcher import ModeSwitcher
import json

setup_logging()

class PresetManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preset_manager = PresetManager()
        self.mode_switcher = ModeSwitcher(self)
        self.init_ui()
        self.refresh_preset_list()

    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle('Управление пресетами')
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Добавляем ModeSwitcher в верхнюю часть окна
        layout.addWidget(self.mode_switcher)
        
        # Добавляем разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Список пресетов
        self.preset_list = QListWidget()
        layout.addWidget(QLabel('Доступные пресеты:'))
        layout.addWidget(self.preset_list)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        
        self.create_btn = QPushButton('Создать')
        self.create_btn.clicked.connect(self.create_preset)
        btn_layout.addWidget(self.create_btn)
        
        self.apply_btn = QPushButton('Применить')
        self.apply_btn.clicked.connect(self.apply_preset)
        btn_layout.addWidget(self.apply_btn)
        
        self.delete_btn = QPushButton('Удалить')
        self.delete_btn.clicked.connect(self.delete_preset)
        btn_layout.addWidget(self.delete_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # Подключаем сигнал изменения режима
        self.mode_switcher.modeChanged.connect(self.on_mode_changed)

    def on_mode_changed(self, mode):
        """Обработчик изменения режима камеры"""
        logging.info(f"Camera mode changed to: {mode}")

    def refresh_preset_list(self):
        """Обновление списка пресетов"""
        self.preset_list.clear()
        presets = self.preset_manager.get_preset_list()
        self.preset_list.addItems(presets)

    def create_preset(self):
        """Создание нового пресета"""
        try:
            # Подключаем камеры по USB
            connect_cameras()
            
            # Получаем список камер
            devices = discover_gopro_devices()
            if not devices:
                QMessageBox.warning(self, 'Ошибка', 'Не найдены подключенные камеры')
                return
                
            # Ильзуем первую камеру для создания пресета
            camera = devices[0]
            
            name, ok = QInputDialog.getText(
                self, 'Новый пресет',
                'Введите название пресета:'
            )
            
            if ok and name:
                if self.preset_manager.create_preset(name, camera['ip']):
                    self.refresh_preset_list()
                    QMessageBox.information(
                        self, 'Успех',
                        f'Пресет "{name}" успешно создан'
                    )
                else:
                    QMessageBox.warning(
                        self, 'Ошибка',
                        'Не удалось создать пресет'
                    )
        except Exception as e:
            logging.error(f"Error creating preset: {e}")
            QMessageBox.critical(
                self, 'Ошибка',
                f'Ошибка при создании пресета: {str(e)}'
            )

    def apply_preset(self):
        """Применение выбранного пресета"""
        try:
            selected = self.preset_list.currentItem()
            if not selected:
                QMessageBox.warning(
                    self, 'Предупреждение',
                    'Выберите пресет для применения'
                )
                return
                
            preset_name = selected.text()
            
            # Подключаем камеры по USB
            connect_cameras()
            
            # Получаем список камер
            devices = discover_gopro_devices()
            if not devices:
                QMessageBox.warning(
                    self, 'Ошибка',
                    'Не найдены подключенные камеры'
                )
                return
            
            # Получаем настройки пресета
            preset_data = self.preset_manager.presets[preset_name]
            settings = preset_data.get("settings", {})
            source_model = preset_data.get("source_model")
            
            # Преобразуем настройки в нужный формат
            formatted_settings = {}
            for setting_id, value in settings.items():
                if isinstance(setting_id, str) and setting_id.isdigit():
                    formatted_settings[int(setting_id)] = value
                else:
                    formatted_settings[setting_id] = value
            
            def copy_function(progress_callback):
                try:
                    if progress_callback:
                        progress_callback("status", f"Applying preset '{preset_name}' to cameras")
                        progress_callback("log", f"Source model: {source_model}")
                        progress_callback("log", f"Total settings to apply: {len(formatted_settings)}")
                    
                    # Используем существующую функцию для пар��ллельного копирования
                    from read_and_write_all_settings_from_prime_to_other import copy_settings_to_camera
                    from concurrent.futures import ThreadPoolExecutor
                    from multiprocessing import Value
                    import ctypes
                    
                    total_cameras = len(devices)
                    total_settings = len(formatted_settings)
                    total_operations = total_cameras * total_settings
                    completed_operations = Value(ctypes.c_int, 0)
                    
                    def camera_progress_callback(action, data):
                        if action == "log":
                            progress_callback("log", data)
                        elif action == "progress":
                            with completed_operations.get_lock():
                                completed_operations.value += 1
                                current_progress = int((completed_operations.value / total_operations) * 100)
                                progress_callback("progress", (current_progress, 100))
                    
                    with ThreadPoolExecutor(max_workers=total_cameras) as executor:
                        futures = []
                        for device in devices:
                            future = executor.submit(
                                copy_settings_to_camera,
                                device,
                                formatted_settings,
                                source_model,
                                camera_progress_callback
                            )
                            futures.append(future)
                        
                        # Wait for all operations to complete
                        for future in futures:
                            try:
                                future.result()
                            except Exception as e:
                                logging.error(f"Error in parallel copy: {e}")
                                if progress_callback:
                                    progress_callback("log", f"\nError: {str(e)}")
                    
                    if progress_callback:
                        progress_callback("complete", None)
                        
                except Exception as e:
                    if progress_callback:
                        progress_callback("log", f"\nError: {str(e)}")
                    raise
            
            # Создаем и показываем диалог прогресса
            progress_dialog = SettingsProgressDialog("Applying Preset", copy_function, self)
            progress_dialog.exec_()
            
        except Exception as e:
            logging.error(f"Error applying preset: {e}")
            QMessageBox.critical(
                self, 'Ошибка',
                f'Ошибка при применении пресета: {str(e)}'
            )

    def delete_preset(self):
        """Удаление выбранного пресета"""
        try:
            selected = self.preset_list.currentItem()
            if not selected:
                QMessageBox.warning(
                    self, 'Предупреждение',
                    'Выберите пресет для удаления'
                )
                return
                
            preset_name = selected.text()
            
            reply = QMessageBox.question(
                self, 'Подтверждение',
                f'Вы уверены, что хотите удалить пресет "{preset_name}"?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.preset_manager.delete_preset(preset_name):
                    self.refresh_preset_list()
                    QMessageBox.information(
                        self, 'Успех',
                        f'Пресет "{preset_name}" успешно удален'
                    )
                else:
                    QMessageBox.warning(
                        self, 'Ошибка',
                        'Не удалось удалить пресет'
                    )
        except Exception as e:
            logging.error(f"Error deleting preset: {e}")
            QMessageBox.critical(
                self, 'Ошибка',
                f'Ошибка при удалении пресета: {str(e)}'
            ) 