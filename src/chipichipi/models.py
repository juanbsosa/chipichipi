from dataclasses import dataclass
from pathlib import Path
from PySide6.QtSql import QSqlTableModel
from PySide6.QtCore import Qt, QModelIndex

@dataclass
class Song:
    """A class to represent a song's metadata."""
    file_path: Path
    title: str = ""
    artist: str = ""
    album: str = ""
    duration: int = 0  # in seconds

    # This method will be useful later for printing/displaying
    def __str__(self):
        return f"{self.artist} - {self.title}"
    

class MusicTableModel(QSqlTableModel):
    """Custom table model for music library with proper data formatting."""
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """Override data method to format specific columns."""
        if not index.isValid():
            return None
        
        # Handle display role for specific columns
        if role == Qt.DisplayRole:
            column = index.column()
            
            # Get the raw value from the parent class
            value = super().data(index, role)
            
            # Format duration column (seconds to MM:SS)
            if column == 6:  # Assuming duration is column 6 (0-based index)
                return self.format_duration(value)
            
            # Format track number column
            elif column == 5:  # Assuming track_number is column 5
                return self.format_track_number(value)
            
            return value
        
        return super().data(index, role)
    
    def format_duration(self, seconds: int) -> str:
        """Convert seconds to MM:SS format."""
        if not seconds or seconds == 0:
            return ""
        
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def format_track_number(self, track_num: int) -> str:
        """Format track number."""
        if not track_num or track_num == 0:
            return ""
        return str(track_num)
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        """Override header data to provide better column names."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            headers = [
                "ID", "File Path", "Title", "Artist", "Album", 
                "Track", "Duration", "Genre"
            ]
            if section < len(headers):
                return headers[section]
        return super().headerData(section, orientation, role)