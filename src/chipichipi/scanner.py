import logging
from pathlib import Path
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
import re
from typing import Tuple, Optional

from chipichipi.models import Song

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Map file extensions to their respective mutagen class
AUDIO_FILE_EXTENSIONS = {
    '.mp3': MP3,
    '.flac': FLAC,
    '.m4a': MP4
}

def get_audio_tag(file: File, tag_name: str) -> str:
    """Safely retrieves a tag from a mutagen file object."""
    try:
        # Tags can be lists of values. We take the first one.
        value = file.tags.get(tag_name)
        return value[0] if value else ""
    except (AttributeError, KeyError, IndexError):
        return ""

def get_audio_duration(audio_file) -> int:
    """Safely retrieves the duration of the audio file in seconds."""
    try:
        if hasattr(audio_file, 'info') and hasattr(audio_file.info, 'length'):
            duration = int(audio_file.info.length)
            logger.debug(f"Duration for {getattr(audio_file, 'filename', 'unknown')}: {duration}s")
            return duration
        return 0
    except (AttributeError, TypeError, ValueError) as e:
        logger.debug(f"Could not get duration: {e}")
        return 0

def scan_file(file_path: Path) -> Song | None:
    """Scans a single audio file and returns a Song object with its metadata."""
    file_extension = file_path.suffix.lower()

    if file_extension not in AUDIO_FILE_EXTENSIONS:
        return None

    audio_file = None
    song = Song(file_path=file_path)

    try:
        # METHOD 1: Try the specific, fast parser first
        specific_class = AUDIO_FILE_EXTENSIONS.get(file_extension)
        if specific_class:
            audio_file = specific_class(file_path)
        
    except Exception as e:
        logger.debug(f"Specific parser failed for {file_path}: {e}. Trying fallback...")
        audio_file = None

    # METHOD 2: If the specific parser failed, use the slow, generic fallback.
    if audio_file is None:
        try:
            audio_file = File(file_path, easy=True)
            logger.info(f"Used fallback parser for: {file_path}")
        except Exception as e:
            logger.warning(f"All parsers failed for file {file_path}: {e}")
            return None

    # If we have a file object (from either method), try to extract tags.
    if audio_file is not None:
        try:
            # Check if the file has tags at all
            if audio_file.tags is None:
                logger.info(f"File has no tags: {file_path}. Will use filename parsing.")
                # Set empty values and rely on filename parsing later
                song.title = file_path.stem
                song.artist = ""
                song.album = ""
            else:
                # Extract tags using the fallback method with safe defaults
                song.title = clean_metadata_value(str(audio_file.tags.get('title', [file_path.stem])[0]))
                song.artist = clean_metadata_value(str(audio_file.tags.get('artist', [''])[0]))
                song.album = clean_metadata_value(str(audio_file.tags.get('album', [''])[0]))
            
                    
            # Get duration (this should work even if no tags)
            song.duration = get_audio_duration(audio_file)

            # NEW: Smart fallback - if artist is missing/empty, try to parse from filename
            if not song.artist or song.artist.strip() in ['', 'Unknown Artist']:
                artist_from_filename, title_from_filename = parse_artist_title_from_filename(file_path.name)
                
                if artist_from_filename and title_from_filename:
                    logger.info(f"Extracted from filename: {artist_from_filename} - {title_from_filename}")
                    song.artist = artist_from_filename
                    # Only update title if it's the default (filename stem) or empty
                    if song.title == file_path.stem or not song.title.strip():
                        song.title = title_from_filename

            logger.info(f"Scanned: {song.artist} - {song.title}")
            return song

        except Exception as e:
            logger.error(f"Error extracting tags from {file_path} (file was opened): {e}")
            return None

def scan_directory(root_path: Path, db_conn) -> None:
    """Recursively scans a directory for audio files and adds them to the database."""
    root_path = Path(root_path)

    if not root_path.is_dir():
        raise ValueError(f"The path {root_path} is not a valid directory.")

    logger.info(f"Starting scan of directory: {root_path}")

    # Find all audio files
    audio_files = []
    for file_path in root_path.rglob('*'):
        if file_path.suffix.lower() in AUDIO_FILE_EXTENSIONS:
            audio_files.append(file_path)

    logger.info(f"Found {len(audio_files)} audio files to process")

    # Process each file
    for file_path in audio_files:
        song = scan_file(file_path)
        if song:
            from chipichipi.database import insert_song
            insert_song(db_conn, song)

    logger.info("Directory scan complete.")

def parse_artist_title_from_filename(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Attempt to extract artist and title from filename.
    """
    # Remove file extension and clean up the filename
    base_name = re.sub(r'\.(mp3|flac|m4a|wav|aiff|ogg)$', '', filename, flags=re.IGNORECASE)
    base_name = base_name.strip()
    
    # Try different separator patterns in order of likelihood
    patterns = [
        r'^(.*?)\s*[-–—]\s*(.*)$',  # Most common: "Artist - Title" with optional spaces
        r'^(.*?)\s+by\s+(.*)$',     # "Artist by Title" pattern
        r'^(.*?)[_](.*)$',          # Underscore separator: "Artist_Title"
        r'^(.*?)\s*\(\s*(.*)$',     # Parentheses: "Artist (Title)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, base_name, re.IGNORECASE)
        if match:
            artist = match.group(1).strip()
            title = match.group(2).strip()
            
            # Basic validation - both should have meaningful content
            if (artist and title and 
                len(artist) > 1 and len(title) > 1 and
                not artist.isdigit() and not title.isdigit()):
                return artist, title
    
    return None, None


def clean_metadata_value(value: str) -> str:
    """Clean up metadata values by removing common issues."""
    if value is None:
        return ""
    
    value = str(value).strip()
    
    # Remove null characters and other weird artifacts
    value = value.replace('\x00', '')
    
    # Remove excessive whitespace
    value = re.sub(r'\s+', ' ', value)
    
    return value