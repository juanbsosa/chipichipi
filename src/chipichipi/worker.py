import logging
from pathlib import Path
from PySide6.QtCore import QObject, Signal

from chipichipi.database import get_db_connection, init_db
from chipichipi.scanner import scan_directory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScannerWorker(QObject):
    """Worker class to handle scanning in a separate thread."""
    
    # Signals to communicate with the main thread
    started = Signal()
    finished = Signal()
    error = Signal(str)
    progress = Signal(str)  # Emit progress messages
    count_updated = Signal(int)  # Emit new song count

    def __init__(self, db_path: Path):
        super().__init__()
        self.db_path = db_path
        self._is_running = False

    def scan(self, directory_path: Path):
        """Perform the scan operation."""
        if self._is_running:
            self.error.emit("Scan already in progress")
            return

        self._is_running = True
        self.started.emit()
        
        try:
            # Initialize database
            init_db(self.db_path)
            conn = get_db_connection(self.db_path)
            
            try:
                # Scan the directory
                self.progress.emit(f"Scanning: {directory_path}")
                scan_directory(directory_path, conn)
                
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