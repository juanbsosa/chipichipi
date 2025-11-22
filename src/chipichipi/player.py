import pygame
import time
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QThread
import logging

logger = logging.getLogger(__name__)

class AudioPlayer(QObject):
    """Audio player using pygame for playback."""
    
    # Signals to communicate with the main thread
    playback_started = Signal()
    playback_paused = Signal()
    playback_stopped = Signal()
    playback_ended = Signal()
    position_changed = Signal(float)  # Current position in seconds
    duration_changed = Signal(float)  # Total duration in seconds
    
    def __init__(self):
        super().__init__()
        self._initialize_pygame()
        self.current_file = None
        self.is_playing = False
        self.is_paused = False
        self.duration = 0.0
        self.position = 0.0
        
    def _initialize_pygame(self):
        """Initialize pygame mixer with optimal settings for MP3 playback."""
        try:
            # Quit any existing mixer
            pygame.mixer.quit()
            
            # Initialize with specific settings that work better with MP3s
            # frequency=44100, size=-16, channels=2, buffer=1024
            pygame.mixer.pre_init(
                frequency=44100,    # CD quality sample rate
                size=-16,          # 16-bit signed samples
                channels=2,        # Stereo
                buffer=1024        # Smaller buffer for less latency
            )
            pygame.mixer.init()
            
            logger.info(f"Pygame mixer initialized: {pygame.mixer.get_init()}")
            
        except Exception as e:
            logger.error(f"Failed to initialize pygame mixer: {e}")
            # Try with default settings as fallback
            try:
                pygame.mixer.init()
                logger.info("Pygame mixer initialized with default settings")
            except Exception as e2:
                logger.error(f"Failed to initialize pygame mixer with defaults: {e2}")
                raise
                
    def reinitialize_mixer(self):
        """Reinitialize pygame mixer - useful for troubleshooting."""
        try:
            was_playing = self.is_playing
            if was_playing:
                self.stop()
                
            self._initialize_pygame()
            
            logger.info("Pygame mixer reinitialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reinitialize mixer: {e}")
            return False
        
    def load_file(self, file_path: Path):
        """Load an audio file for playback."""
        try:
            if self.is_playing:
                self.stop()
            
            # Validate file exists and is readable
            if not file_path.exists():
                logger.error(f"File does not exist: {file_path}")
                return False
            
            if not file_path.is_file():
                logger.error(f"Path is not a file: {file_path}")
                return False
            
            # Validate file with mutagen first
            from mutagen import File
            try:
                audio_file = File(file_path)
                if audio_file is None:
                    logger.error(f"File is not a valid audio file: {file_path}")
                    return False
                    
                # Get duration using mutagen
                if hasattr(audio_file, 'info') and hasattr(audio_file.info, 'length'):
                    self.duration = audio_file.info.length
                    logger.info(f"Audio file duration: {self.duration:.2f}s")
                else:
                    self.duration = 0
                    logger.warning(f"Could not determine duration for: {file_path}")
                    
            except Exception as e:
                logger.error(f"Mutagen validation failed for {file_path}: {e}")
                return False
            
            # Try to load with pygame
            try:
                # Convert path to string and handle any special characters
                file_str = str(file_path.absolute())
                pygame.mixer.music.load(file_str)
                
                self.current_file = file_path
                self.duration_changed.emit(self.duration)
                self.position = 0.0
                self.position_changed.emit(self.position)
                
                logger.info(f"Successfully loaded audio file: {file_path.name}")
                return True
                
            except pygame.error as e:
                error_msg = str(e).lower()
                if 'corrupt mp3' in error_msg or 'bad stream' in error_msg:
                    logger.error(f"MP3 decoding error for {file_path}: {e}")
                    logger.info("This may be due to pygame's limited MP3 decoder. Consider converting to OGG or WAV format.")
                else:
                    logger.error(f"Pygame loading error for {file_path}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error loading file {file_path}: {e}")
            return False
    
    def play(self):
        """Start or resume playback."""
        try:
            if not self.current_file:
                logger.error("No file loaded for playback")
                return False
                
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                logger.info("Resumed playback")
            else:
                pygame.mixer.music.play()
                logger.info(f"Started playback of: {self.current_file.name}")
                
            self.is_playing = True
            self.playback_started.emit()
            
            # Start position tracking thread
            self.start_position_tracking()
            return True
            
        except pygame.error as e:
            logger.error(f"Pygame playback error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during playback: {e}")
            return False
    
    def pause(self):
        """Pause playback."""
        try:
            if self.is_playing and not self.is_paused:
                pygame.mixer.music.pause()
                self.is_paused = True
                self.playback_paused.emit()
        except Exception as e:
            logger.error(f"Error pausing audio: {e}")
    
    def stop(self):
        """Stop playback."""
        try:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            self.position = 0.0
            self.position_changed.emit(self.position)
            self.playback_stopped.emit()
            
        except Exception as e:
            logger.error(f"Error stopping audio: {e}")
    
    def set_position(self, position: float):
        """Set playback position in seconds."""
        try:
            pygame.mixer.music.set_pos(position)
            self.position = position
            self.position_changed.emit(position)
        except Exception as e:
            logger.error(f"Error setting position: {e}")
    
    def start_position_tracking(self):
        """Start a thread to track playback position."""
        def track_position():
            while self.is_playing and not self.is_paused:
                try:
                    # Get current position (this is approximate)
                    if pygame.mixer.music.get_busy():
                        # Estimate position based on playback start time
                        # Note: pygame doesn't provide exact position tracking
                        # This is an approximation
                        self.position += 0.1  # Update every 100ms
                        if self.position > self.duration:
                            self.position = self.duration
                            self.stop()
                            self.playback_ended.emit()
                        else:
                            self.position_changed.emit(self.position)
                    time.sleep(0.1)  # Update every 100ms
                except:
                    break
        
        # Start tracking in a separate thread
        self.tracking_thread = QThread()
        self.tracking_thread.run = track_position
        self.tracking_thread.start()
    
    def get_volume(self):
        """Get current volume (0.0 to 1.0)."""
        return pygame.mixer.music.get_volume()
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        try:
            pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        self.stop()
        pygame.mixer.quit()