import logging
from pathlib import Path
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC

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

def get_audio_duration(file: File) -> int:
    """Safely retrieves the duration of the audio file in seconds."""
    try:
        duration = int(file.info.length)
        print(f"DEBUG: Duration for {file} is {duration} seconds")  # Debug output
        return duration
    except AttributeError as e:
        print(f"DEBUG: Could not get duration: {e}")  # Debug output
        return 0

def scan_file(file_path: Path) -> Song | None:
    """Scans a single audio file and returns a Song object with its metadata."""
    file_extension = file_path.suffix.lower()

    # First, check if the extension is one we even want to try
    if file_extension not in AUDIO_FILE_EXTENSIONS:
        return None

    audio_file = None
    song = Song(file_path=file_path)

    try:
        # METHOD 1: Try the specific, fast parser first (e.g., mutagen.mp3.MP3)
        specific_class = AUDIO_FILE_EXTENSIONS.get(file_extension)
        if specific_class:
            audio_file = specific_class(file_path)
        
    except Exception as e:
        logger.debug(f"Specific parser failed for {file_path}: {e}. Trying fallback...")
        audio_file = None

    # METHOD 2: If the specific parser failed, use the slow, generic fallback.
    # mutagen.File() is less efficient but much more tolerant of file errors.
    if audio_file is None:
        try:
            audio_file = File(file_path, easy=True) # `easy=True` gives a simple interface
            logger.info(f"Used fallback parser for: {file_path}")
        except Exception as e:
            logger.warning(f"All parsers failed for file {file_path}: {e}")
            return None

    # If we have a file object (from either method), try to extract tags.
    if audio_file is not None:
        try:
            # Check if the file has tags
            if not audio_file.tags:
                logger.info(f"File has no tags: {file_path}. Using filename.")
                song.title = file_path.stem
                song.artist = ""
                return song

            # Extract tags. The fallback `File` object with easy=True uses a simpler API.
            # We can use .get() to safely access tags.
            song.title = str(audio_file.tags.get('title', [file_path.stem])[0])
            song.artist = str(audio_file.tags.get('artist', [''])[0])
            song.album = str(audio_file.tags.get('album', [''])[0])

            logger.info(f"Scanned: {song.artist} - {song.title}")
            return song

        except Exception as e:
            # This catches errors during the tag extraction process itself
            logger.error(f"Error extracting tags from {file_path} (file was opened): {e}")
            return None

def scan_directory(root_path: Path, db_conn) -> None:
    """Recursively scans a directory for audio files and adds them to the database."""
    root_path = Path(root_path)

    if not root_path.is_dir():
        raise ValueError(f"The path {root_path} is not a valid directory.")

    logger.info(f"Starting scan of directory: {root_path}")

    # Use .rglob to recursively find all files
    for file_path in root_path.rglob('*'):
        if file_path.suffix.lower() in AUDIO_FILE_EXTENSIONS:
            song = scan_file(file_path)
            if song:
                # Use the connection passed as an argument
                from chipichipi.database import insert_song # Import here to avoid circular import
                insert_song(db_conn, song) # We need to pass the connection

    logger.info("Directory scan complete.")