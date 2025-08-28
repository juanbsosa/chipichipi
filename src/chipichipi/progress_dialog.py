from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                               QProgressBar, QPushButton, QHBoxLayout)
from PySide6.QtCore import Qt, QTimer, QElapsedTimer

class ScanProgressDialog(QDialog):
    """Dialog to show scanning progress with estimated time."""
    
    def __init__(self, total_files, parent=None):
        super().__init__(parent)
        self.total_files = total_files
        self.processed_files = 0
        self.elapsed_timer = QElapsedTimer()  # Use QElapsedTimer instead
        self.setWindowTitle("Scanning Library")
        self.setModal(True)
        self.setFixedSize(400, 150)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the progress dialog UI."""
        layout = QVBoxLayout(self)
        
        # Status label
        self.status_label = QLabel("Preparing to scan...")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.total_files)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Details label (shows ETA and current file)
        self.details_label = QLabel("")
        self.details_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.details_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
    def update_progress(self, current_file_path, processed_count):
        """Update the progress with current file and count."""
        self.processed_files = processed_count
        self.progress_bar.setValue(processed_count)
        
        # Calculate progress percentage
        progress_percent = (processed_count / self.total_files) * 100
        
        # Update status
        self.status_label.setText(f"Scanning: {processed_count}/{self.total_files} files")
        
        # Calculate ETA if we have start time
        if self.elapsed_timer.isValid() and processed_count > 0:
            elapsed = self.elapsed_timer.elapsed() / 1000  # Convert to seconds
            files_per_second = processed_count / elapsed
            remaining_files = self.total_files - processed_count
            
            if files_per_second > 0:
                eta_seconds = remaining_files / files_per_second
                eta_text = self.format_time(eta_seconds)
                elapsed_text = self.format_time(elapsed)
                self.details_label.setText(
                    f"ETA: {eta_text} | Elapsed: {elapsed_text} | "
                    f"File: {current_file_path.name[:30]}..."
                )
            else:
                self.details_label.setText(f"File: {current_file_path.name[:30]}...")
        else:
            self.details_label.setText(f"File: {current_file_path.name[:30]}...")
    
    def format_time(self, seconds):
        """Format seconds into HH:MM:SS or MM:SS."""
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def start_timer(self):
        """Start the progress timer."""
        self.elapsed_timer.start()
    
    def get_elapsed_time(self):
        """Get elapsed time in seconds."""
        if self.elapsed_timer.isValid():
            return self.elapsed_timer.elapsed() / 1000
        return 0