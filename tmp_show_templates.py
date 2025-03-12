from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QTableWidget, QTableWidgetItem, QHeaderView
)
from pathlib import Path
import os
import json
from datetime import datetime
import sys

class TemplateViewerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Template Viewer')
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Mode', 'Name', 'Date Created', 'Settings Count'])
        
        # Set column stretch
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Mode
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Count
        
        layout.addWidget(self.table)
        
        # Load templates
        self.load_templates()
        
    def load_templates(self):
        """Load and display templates"""
        try:
            # Get templates directory
            current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
            templates_dir = current_dir / 'camera_templates'
            
            if not templates_dir.exists():
                print(f"Templates directory not found: {templates_dir}")
                return
            
            # Mode prefixes
            modes = {
                'video_': 'VIDEO',
                'photo_': 'PHOTO',
                'timelapse_': 'TIMELAPSE'
            }
            
            # Find all JSON files
            template_files = list(templates_dir.glob('*.json'))
            
            # Set table rows
            self.table.setRowCount(len(template_files))
            
            # Fill table
            for row, template_file in enumerate(sorted(template_files)):
                try:
                    # Get mode from prefix
                    mode = 'UNKNOWN'
                    name = template_file.stem
                    for prefix, mode_name in modes.items():
                        if template_file.name.startswith(prefix):
                            mode = mode_name
                            name = template_file.stem[len(prefix):]  # Remove prefix
                            break
                    
                    # Load template to get metadata
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    
                    # Get creation date
                    try:
                        date_str = template_data.get('metadata', {}).get('scan_date', '')
                        if date_str:
                            date = datetime.fromisoformat(date_str).strftime('%Y-%m-%d %H:%M')
                        else:
                            date = datetime.fromtimestamp(os.path.getctime(template_file)).strftime('%Y-%m-%d %H:%M')
                    except:
                        date = 'Unknown'
                    
                    # Get settings count
                    settings_count = len(template_data.get('settings', {}))
                    
                    # Add items to table
                    self.table.setItem(row, 0, QTableWidgetItem(mode))
                    self.table.setItem(row, 1, QTableWidgetItem(name))
                    self.table.setItem(row, 2, QTableWidgetItem(date))
                    self.table.setItem(row, 3, QTableWidgetItem(str(settings_count)))
                    
                except Exception as e:
                    print(f"Error reading template {template_file.name}: {e}")
                    # Add error row
                    self.table.setItem(row, 0, QTableWidgetItem('ERROR'))
                    self.table.setItem(row, 1, QTableWidgetItem(template_file.name))
                    self.table.setItem(row, 2, QTableWidgetItem('Error'))
                    self.table.setItem(row, 3, QTableWidgetItem('Error'))
        
        except Exception as e:
            print(f"Error loading templates: {e}")

def main():
    app = QApplication(sys.argv)
    window = TemplateViewerWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 