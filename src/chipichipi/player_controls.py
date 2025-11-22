from PySide6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, 
                               QSlider, QLabel, QVBoxLayout)
from PySide6.QtCore import Qt, Signal
from pathlib import Path

class PlayerControls(QWidget):
    """Widget containing audio player controls."""
    
    play_requested = Signal()
    pause_requested = Signal()
    stop_requested = Signal()
    position_change_requested = Signal(float)
    volume_change_requested = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the player controls UI."""
        layout = QVBoxLayout(self)
        
        # Playback controls
        controls_layout = QHBoxLayout()
        
        self.play_button = QPushButton("▶")
        self.play_button.clicked.connect(self.play_requested.emit)
        self.play_button.setFixedSize(40, 40)
        
        self.pause_button = QPushButton("⏸")
        self.pause_button.clicked.connect(self.pause_requested.emit)
        self.pause_button.setFixedSize(40, 40)
        
        self.stop_button = QPushButton("⏹")
        self.stop_button.clicked.connect(self.stop_requested.emit)
        self.stop_button.setFixedSize(40, 40)
        
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)
        
        # Progress slider
        progress_layout = QVBoxLayout()
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderMoved.connect(self._on_slider_moved)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(self.time_label)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(
            lambda value: self.volume_change_requested.emit(value / 100.0)
        )
        volume_layout.addWidget(self.volume_slider)
        
        # Add all layouts to main layout
        layout.addLayout(controls_layout)
        layout.addLayout(progress_layout)
        layout.addLayout(volume_layout)
    
    def _on_slider_moved(self, value):
        """Handle slider movement."""
        position = value / 1000.0
        self._update_time_label(position, None)
    
    def _on_slider_released(self):
        """Handle slider release - seek to position."""
        position = self.progress_slider.value() / 1000.0
        self.position_change_requested.emit(position)
    
    def update_position(self, position: float, duration: float):
        """Update the progress display."""
        if duration > 0:
            progress = int((position / duration) * 1000)
            self.progress_slider.setValue(progress)
        self._update_time_label(position, duration)
    
    def _update_time_label(self, position: float, duration: float):
        """Update the time display label."""
        pos_text = self._format_time(position)
        dur_text = self._format_time(duration) if duration is not None else "00:00"
        self.time_label.setText(f"{pos_text} / {dur_text}")
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds into MM:SS."""
        if seconds is None:
            return "00:00"
        seconds = int(seconds)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def set_playing_state(self, is_playing: bool, is_paused: bool):
        """Update button states based on playback state."""
        self.play_button.setEnabled(not is_playing or is_paused)
        self.pause_button.setEnabled(is_playing and not is_paused)
        self.stop_button.setEnabled(is_playing)