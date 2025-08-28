import sys
from pathlib import Path

from PySide6.QtWidgets import (QApplication, QMainWindow, QTableView, 
                               QVBoxLayout, QWidget, QHeaderView)
from PySide6.QtSql import QSqlDatabase, QSqlTableModel
from PySide6.QtCore import Qt, QThread

import logging

from chipichipi.worker import ScannerWorker
from chipichipi.models import MusicTableModel
from chipichipi.progress_dialog import ScanProgressDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChipiChipi Music Manager")
        self.setGeometry(100, 100, 1000, 600)
        
        # Database path
        self.db_path = Path("music_library.db")
        
        # Scanner thread and worker
        self.scanner_thread = None
        self.scanner_worker = None
        
        self.setup_ui()
        self.setup_database()
        
    def setup_ui(self):
        """Set up the user interface."""
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create the table view
        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        # Create menu bar
        self.setup_menu()
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
    def setup_menu(self):
        """Set up the menu bar."""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        # Add actions
        scan_action = file_menu.addAction("&Scan Directory")
        scan_action.triggered.connect(self.on_scan_directory)
        scan_action.setShortcut("Ctrl+S")

        refresh_action = file_menu.addAction("&Refresh")
        refresh_action.triggered.connect(self.refresh_library)
        refresh_action.setShortcut("Ctrl+R")

        file_menu.addSeparator()
        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Ctrl+Q")
        
    def setup_database(self):
        """Initialize the database connection and set up the model."""
        # Create a connection to the SQLite database
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(str(self.db_path.absolute()))

        if not self.db.open():
            self.statusBar().showMessage("Failed to open database!")
            return

        # Use our improved model creation
        if not self.recreate_model():
            self.statusBar().showMessage("Failed to create model!")
            return
        
        # Show song count in status bar
        self.update_song_count()
        
    def update_song_count(self):
        """Update the song count in the status bar."""
        if self.db.isOpen():
            # Use QSqlQuery instead of cursor()
            query = self.db.exec("SELECT COUNT(*) FROM songs")
            if query.first():  # Move to the first result
                count = query.value(0)  # Get the value of the first column
                self.statusBar().showMessage(f"Ready - {count} songs in library")
            else:
                self.statusBar().showMessage("Ready - No songs in library")
            
    def refresh_library(self):
        """Refresh the library view to show current database state."""
        if self.recreate_model():
            self.update_song_count()
            self.statusBar().showMessage("Library completely refreshed", 2000)

    def recreate_model(self):
        """Completely recreate the model (more thorough refresh)."""
        if hasattr(self, 'model'):
            # Clean up old model
            self.model.deleteLater()
        
        # Use our custom model instead of QSqlTableModel
        self.model = MusicTableModel(db=self.db)
        self.model.setTable("songs")
        
        if not self.model.select():
            error = self.model.lastError().text()
            self.statusBar().showMessage(f"Model error: {error}")
            return False
        
        # Set the new model
        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSortingEnabled(True)
        
        # Set column resize modes
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)       # File Path
        self.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)           # Title
        self.table_view.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)           # Artist
        self.table_view.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)           # Album
        self.table_view.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Duration
        
        # Hide the ID column (column 0) if desired
        self.table_view.hideColumn(0)
        
        return True
            
    def on_scan_directory(self):
        """Handle the Scan Directory menu action."""
        from PySide6.QtWidgets import QFileDialog
        
        # Check if a scan is already running
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.statusBar().showMessage("Scan already in progress!")
            return
            
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Scan")
        
        if directory:
            self.start_scan(Path(directory))
            
    def start_scan(self, directory_path: Path):
        """Start the scanning process in a separate thread."""
        # Create thread and worker
        self.scanner_thread = QThread()
        self.scanner_worker = ScannerWorker(self.db_path)
        
        # Move worker to thread
        self.scanner_worker.moveToThread(self.scanner_thread)
        
        # Connect signals
        self.scanner_worker.started.connect(self.on_scan_started)
        self.scanner_worker.finished.connect(self.on_scan_finished)
        self.scanner_worker.error.connect(self.on_scan_error)
        self.scanner_worker.progress.connect(self.on_scan_progress)
        self.scanner_worker.count_updated.connect(self.on_count_updated)
        
        # Connect new progress signals
        self.scanner_worker.total_files_found.connect(self.on_total_files_found)
        self.scanner_worker.file_processed.connect(self.on_file_processed)
        
        # Connect thread start to worker scan method
        self.scanner_thread.started.connect(
            lambda: self.scanner_worker.scan(directory_path)
        )
        
        # Clean up when thread finishes
        self.scanner_thread.finished.connect(self.scanner_thread.deleteLater)
        
        # Create progress dialog (but don't show it yet)
        self.progress_dialog = None
        self.total_files = 0  # Initialize total files counter
        
        # Start the thread
        self.scanner_thread.start()

    def on_total_files_found(self, total_files):
        """Handle total files found signal - create and show progress dialog."""
        self.total_files = total_files
        if self.progress_dialog is None:
            self.progress_dialog = ScanProgressDialog(total_files, self)
            self.progress_dialog.cancel_button.clicked.connect(self.cancel_scan)
            self.progress_dialog.start_timer()
            self.progress_dialog.show()

    def on_file_processed(self, current_file, processed_count, total_files):
        """Handle file processed signal - update progress dialog."""
        if self.progress_dialog and self.progress_dialog.isVisible():
            self.progress_dialog.update_progress(current_file, processed_count)

    def on_scan_started(self):
        """Handle scan started signal."""
        self.statusBar().showMessage("Scanning...")
        # Disable scan action while scanning
        for action in self.menuBar().actions():
            if action.text() and "Scan" in action.text():
                action.setEnabled(False)

    def cancel_scan(self):
        """Cancel the ongoing scan."""
        if self.scanner_worker:
            self.scanner_worker.cancel()
        if self.progress_dialog:
            self.progress_dialog.close()

    def on_scan_finished(self):
        """Handle scan finished signal."""
        # Close progress dialog if it's open
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.statusBar().showMessage("Scan completed successfully")
        # Re-enable scan action
        for action in self.menuBar().actions():
            if action.text() and "Scan" in action.text():
                action.setEnabled(True)
        
        # Refresh the library view
        self.refresh_library()
        
        # Clean up thread
        if self.scanner_thread:
            self.scanner_thread.quit()
            self.scanner_thread.wait()
            self.scanner_thread = None
            self.scanner_worker = None
            
    def on_scan_error(self, error_message: str):
        """Handle scan error signal."""
        # Close progress dialog if it's open
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
            
        self.statusBar().showMessage(f"Error: {error_message}")
        logging.error(error_message)
        
        # Re-enable scan action
        for action in self.menuBar().actions():
            if action.text() and "Scan" in action.text():
                action.setEnabled(True)
                
    def on_scan_progress(self, message: str):
        """Handle scan progress updates."""
        self.statusBar().showMessage(message)
        
    def on_count_updated(self, count: int):
        """Handle song count updates."""
        self.statusBar().showMessage(f"Scan complete! Found {count} songs total.")
        
    def closeEvent(self, event):
        """Handle application closure."""
        # Stop any running scan threads
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.scanner_thread.quit()
            self.scanner_thread.wait()
            
        # Close database connection
        if self.db.isOpen():
            self.db.close()
            
        event.accept()

def main():
    """Create and run the Qt application."""
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()