from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QMessageBox, QInputDialog, QLabel
)
from PyQt5.QtCore import Qt
from camera_presets import PresetManager
import logging
from utils import setup_logging
from goprolist_and_start_usb import discover_gopro_devices, main as connect_cameras
from progress_dialog import SettingsProgressDialog
from mode_switcher import ModeSwitcher

setup_logging()

class PresetManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preset_manager = PresetManager()
        self.init_ui()
        self.refresh_preset_list()

    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle('Управление пресетами')
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Основной layout
        main_layout = QVBoxLayout(self)
        
        # Добавляем слайдер режимов
        self.mode_switcher = ModeSwitcher(self)
        main_layout.addWidget(self.mode_switcher)
        
        # Список пресетов
        self.preset_list = QListWidget()
        main_layout.addWidget(self.preset_list)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        self.create_button = QPushButton('Создать')
        self.apply_button = QPushButton('Применить')
        self.delete_button = QPushButton('Удалить')
        
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.delete_button)
        
        main_layout.addLayout(button_layout)
        
        # Подключаем сигналы
        self.create_button.clicked.connect(self.create_preset)
        self.apply_button.clicked.connect(self.apply_preset)
        self.delete_button.clicked.connect(self.delete_preset)
        
        # Загружаем список пресетов
        self.refresh_preset_list()
        
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
                
            # Используем первую камеру для создания пресета
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
                    
            # Применяем настройки ко всем камерам
            success = True
            for device in devices:
                try:
                    # Проверяем модель камеры
                    response = requests.get(f"http://{device['ip']}:8080/gp/gpControl/info", timeout=5)
                    if response.status_code == 200:
                        camera_info = response.json()
                        camera_model = camera_info.get("info", {}).get("model_name")
                        
                        if camera_model != source_model:
                            logging.warning(f"Camera model mismatch: Preset from {source_model}, applying to {camera_model}")
                            
                        # Применяем каждую настройку
                        for setting_id, value in formatted_settings.items():
                            setting_url = f"http://{device['ip']}:8080/gp/gpControl/setting/{setting_id}/{value}"
                            setting_response = requests.get(setting_url, timeout=5)
                            
                            if setting_response.status_code != 200:
                                logging.error(f"Failed to apply setting {setting_id}={value} to camera {device['name']}")
                                success = False
                            else:
                                logging.info(f"Setting {setting_id} successfully set to {value}")
                                
                except Exception as e:
                    logging.error(f"Error applying preset to camera {device['name']}: {e}")
                    success = False
                    
            if success:
                QMessageBox.information(
                    self, 'Успех',
                    f'Пресет "{preset_name}" успешно применен ко всем камерам'
                )
            else:
                QMessageBox.warning(
                    self, 'Предупреждение',
                    'Возникли ошибки при применении пресета. Проверьте лог.'
                )
                
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
                        'Не удалось удалит�� пресет'
                    )
        except Exception as e:
            logging.error(f"Error deleting preset: {e}")
            QMessageBox.critical(
                self, 'Ошибка',
                f'Ошибка при удалении пресета: {str(e)}'
            ) 