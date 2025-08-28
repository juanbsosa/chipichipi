import logging
import time
from pathlib import Path
from PySide6.QtCore import QObject, Signal

from chipichipi.database import get_db_connection, init_db
from chipichipi.scanner import scan_file, scan_directory  # Add scan_file import

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScannerWorker(QObject):
    """Worker class to handle scanning in a separate thread."""
    
    # Signals to communicate with the main thread
    started = Signal()
    finished = Signal()
    error = Signal(str)
    progress = Signal(str)
    count_updated = Signal(int)
    
    # New signals for progress dialog
    total_files_found = Signal(int)  # Emit total number of files found
    file_processed = Signal(Path, int, int)  # Emit (current_file, processed_count, total_files)

    def __init__(self, db_path: Path):
        super().__init__()
        self.db_path = db_path
        self._is_running = False
        self.should_cancel = False

    def scan(self, directory_path: Path):
        """Perform the scan operation."""
        if self._is_running:
            self.error.emit("Scan already in progress")
            return

        self._is_running = True
        self.should_cancel = False
        self.started.emit()
        
        try:
            # Initialize database
            init_db(self.db_path)
            conn = get_db_connection(self.db_path)
            
            try:
                # First, count all audio files to get total
                audio_files = []
                for file_path in directory_path.rglob('*'):
                    if file_path.suffix.lower() in ['.mp3', '.flac', '.m4a', '.wav', '.aiff']:
                        audio_files.append(file_path)

                total_files = len(audio_files)
                self.total_files_found.emit(total_files)
                self.progress.emit(f"Found {total_files} audio files to process")

                # Now process each file
                for index, file_path in enumerate(audio_files):
                    if self.should_cancel:
                        self.progress.emit("Scan cancelled by user")
                        return
                    
                    # Emit progress for this file
                    self.file_processed.emit(file_path, index + 1, total_files)
                    
                    song = scan_file(file_path)  # This should work now
                    if song:
                        from chipichipi.database import insert_song
                        insert_song(conn, song)  # Fixed variable name from db_conn to conn

                # Check if operation was cancelled
                if self.should_cancel:
                    self.progress.emit("Scan cancelled by user")
                    return
                
                # Get the new count of songs
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM songs")
                count = cursor.fetchone()[0]
                self.count_updated.emit(count)
                
                self.progress.emit(f"Scan complete! Found {count} songs.")
                
            finally:
                conn.close()
                
        except Exception as e:
            error_msg = f"Scan failed: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)
        finally:
            self._is_running = False
            self.finished.emit()
    
    def cancel(self):
        """Cancel the ongoing scan operation."""
        self.should_cancel = True