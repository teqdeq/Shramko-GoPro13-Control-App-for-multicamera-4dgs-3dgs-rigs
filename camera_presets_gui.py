from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QComboBox, QLabel, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt
import sys
from camera_presets import PresetManager
from datetime import datetime

class PresetManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Camera Presets Manager')
        self.setMinimumWidth(1000)
        self.setMinimumHeight(600)
        
        # Initialize preset manager
        self.preset_manager = PresetManager()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Mode selector
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel('Mode:'))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(['All', 'Video', 'Photo', 'Timelapse'])
        self.mode_combo.currentTextChanged.connect(self.refresh_presets)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            'Mode', 'Name', 'Description', 'Camera Model', 
            'Created', 'Settings'
        ])
        
        # Set column stretch
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Mode
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Name
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Description
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Camera Model
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Created
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Settings
        
        layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        create_btn = QPushButton('Create Preset')
        create_btn.clicked.connect(self.create_preset)
        btn_layout.addWidget(create_btn)
        
        apply_btn = QPushButton('Apply Preset')
        apply_btn.clicked.connect(self.apply_preset)
        btn_layout.addWidget(apply_btn)
        
        delete_btn = QPushButton('Delete Preset')
        delete_btn.clicked.connect(self.delete_preset)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        
        # Initial load
        self.refresh_presets()
    
    def refresh_presets(self):
        """Refresh the presets list"""
        try:
            # Get selected mode
            mode = self.mode_combo.currentText().lower()
            if mode == 'all':
                mode = None
            
            # Get presets
            presets = self.preset_manager.get_preset_list(mode)
            
            # Update table
            self.table.setRowCount(len(presets))
            
            for row, preset in enumerate(presets):
                self.table.setItem(row, 0, QTableWidgetItem(preset['mode'].upper()))
                self.table.setItem(row, 1, QTableWidgetItem(preset['name']))
                self.table.setItem(row, 2, QTableWidgetItem(preset['description']))
                self.table.setItem(row, 3, QTableWidgetItem(preset['camera_model']))
                
                # Format date
                try:
                    date = datetime.fromisoformat(preset['created_at']).strftime('%Y-%m-%d %H:%M')
                except:
                    date = preset['created_at']
                self.table.setItem(row, 4, QTableWidgetItem(date))
                
                self.table.setItem(row, 5, QTableWidgetItem(str(preset['settings_count'])))
        
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error refreshing presets: {str(e)}')
    
    def get_selected_preset(self):
        """Get selected preset info"""
        row = self.table.currentRow()
        if row < 0:
            return None
            
        return {
            'mode': self.table.item(row, 0).text().lower(),
            'name': self.table.item(row, 1).text()
        }
    
    def create_preset(self):
        """Create new preset"""
        try:
            # Get camera IP
            ip, ok = QInputDialog.getText(
                self, 'Create Preset',
                'Enter camera IP address:'
            )
            if not ok or not ip:
                return
            
            # Get preset name
            name, ok = QInputDialog.getText(
                self, 'Create Preset',
                'Enter preset name (use only English letters, numbers and underscore):'
            )
            if not ok or not name:
                return
                
            # Get mode
            mode, ok = QInputDialog.getItem(
                self, 'Create Preset',
                'Select mode:',
                ['video', 'photo', 'timelapse'],
                0, False
            )
            if not ok:
                return
                
            # Get description
            description, ok = QInputDialog.getText(
                self, 'Create Preset',
                'Enter preset description (optional):'
            )
            if not ok:
                return
            
            # Create preset
            if self.preset_manager.create_preset(name, ip, mode, description):
                self.refresh_presets()
                QMessageBox.information(self, 'Success', 'Preset created successfully')
            else:
                QMessageBox.critical(self, 'Error', 'Failed to create preset')
                
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error creating preset: {str(e)}')
    
    def apply_preset(self):
        """Apply selected preset"""
        try:
            preset = self.get_selected_preset()
            if not preset:
                QMessageBox.warning(self, 'Warning', 'Please select a preset')
                return
            
            # Get camera IP
            ip, ok = QInputDialog.getText(
                self, 'Apply Preset',
                'Enter camera IP address:'
            )
            if not ok or not ip:
                return
            
            # Apply preset
            if self.preset_manager.apply_preset_to_camera(preset['name'], preset['mode'], ip):
                QMessageBox.information(self, 'Success', 'Preset applied successfully')
            else:
                QMessageBox.critical(self, 'Error', 'Failed to apply preset')
                
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error applying preset: {str(e)}')
    
    def delete_preset(self):
        """Delete selected preset"""
        try:
            preset = self.get_selected_preset()
            if not preset:
                QMessageBox.warning(self, 'Warning', 'Please select a preset')
                return
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, 'Confirm Delete',
                f'Are you sure you want to delete preset "{preset["name"]}"?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.preset_manager.delete_preset(preset['name'], preset['mode']):
                    self.refresh_presets()
                    QMessageBox.information(self, 'Success', 'Preset deleted successfully')
                else:
                    QMessageBox.critical(self, 'Error', 'Failed to delete preset')
                    
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error deleting preset: {str(e)}')

def main():
    app = QApplication(sys.argv)
    window = PresetManagerWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 