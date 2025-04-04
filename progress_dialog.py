from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QProgressBar, 
    QLabel, QTextEdit, QPushButton, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor

class CopySettingsThread(QThread):
    status_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    log_signal = pyqtSignal(str)
    complete_signal = pyqtSignal()
    error_signal = pyqtSignal(str)
    
    def __init__(self, copy_function):
        super().__init__()
        self.copy_function = copy_function
        self.is_running = True
        
    def run(self):
        try:
            def progress_callback(action, data):
                if not self.is_running:
                    return True  # Signal cancellation
                    
                if action == "status":
                    self.status_signal.emit(data)
                elif action == "progress":
                    current, total = data
                    self.progress_signal.emit(current, total)
                elif action == "log":
                    self.log_signal.emit(data)
                elif action == "complete":
                    self.complete_signal.emit()
                    
                QApplication.processEvents()
                return False  # Continue execution
                
            # Add a method to check for cancellation in the callback
            progress_callback.was_cancelled = lambda: not self.is_running
            
            result = self.copy_function(progress_callback)
            if not result and self.is_running:
                self.error_signal.emit("Operation failed")
                
        except Exception as e:
            if self.is_running:
                self.error_signal.emit(str(e))
            
    def stop(self):
        self.is_running = False

class SettingsProgressDialog(QDialog):
    def __init__(self, title, copy_function, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.copy_function = copy_function
        self.setup_ui()
        self.setup_thread()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Status
        self.status_label = QLabel("Initializing...")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(400)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.log_text)
        
        # Close button (initially hidden)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_dialog)
        self.close_button.hide()
        layout.addWidget(self.close_button)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_operation)
        layout.addWidget(self.cancel_button)
        
        # Set dialog size
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

    def setup_thread(self):
        self.thread = CopySettingsThread(self.copy_function)
        self.thread.status_signal.connect(self.update_status)
        self.thread.progress_signal.connect(self.update_progress)
        self.thread.log_signal.connect(self.add_log)
        self.thread.complete_signal.connect(self.complete)
        self.thread.error_signal.connect(self.handle_error)
        self.thread.finished.connect(self.on_thread_finished)
        
    def showEvent(self, event):
        super().showEvent(event)
        QApplication.processEvents()
        self.thread.start()
        
    def update_status(self, status):
        self.status_label.setText(status)
        QApplication.processEvents()
        
    def update_progress(self, current, total):
        """Update the progress bar"""
        try:
            if total > 0:
                progress = int((current / total) * 100)
                self.progress_bar.setValue(progress)
                QApplication.processEvents()
        except Exception as e:
            print(f"Error updating progress: {e}")
            
    def add_log(self, message):
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(message + "\n")
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()
        QApplication.processEvents()
        
    def complete(self):
        """Called when operation is complete"""
        self.close_button.show()
        self.cancel_button.hide()
        self.status_label.setText("Operation completed successfully")
        # Set progress to 100% only on successful completion
        self.progress_bar.setValue(100)
        QApplication.processEvents()
        # Automatically close the dialog
        self.close()
        
    def handle_error(self, error_message):
        """Handle error during operation"""
        self.add_log(f"\nError: {error_message}")
        self.close_button.show()
        self.cancel_button.hide()
        self.status_label.setText("Operation failed")
        # Reset progress on error
        self.progress_bar.setValue(0)
        QApplication.processEvents()
        
    def cancel_operation(self):
        """Cancel the operation"""
        self.setWindowTitle("Operation cancelled by user")
        self.status_label.setText("Operation cancelled by user")
        self.add_log("\nOperation cancelled by user")
        self.cancel_button.setEnabled(False)
        # Reset progress on cancellation
        self.progress_bar.setValue(0)
        self.thread.stop()
        QApplication.processEvents()
        
    def close_dialog(self):
        if self.thread.isRunning():
            self.thread.stop()
            self.thread.wait()
        self.accept()
        
    def on_thread_finished(self):
        self.cancel_button.hide()
        self.close_button.show()
        QApplication.processEvents()
        
    def closeEvent(self, event):
        """Handle window close event"""
        if self.thread.isRunning():
            self.cancel_operation()
            self.thread.wait(1000)  # Wait for the thread to finish, max 1 second
        super().closeEvent(event)