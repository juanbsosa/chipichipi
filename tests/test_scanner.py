from pathlib import Path
from chipichipi.scanner import scan_file
from chipichipi.models import Song

def test_scan_file(tmp_path):
    # Create a mock file path to test the extension filtering
    non_audio_file = tmp_path / "test.txt"
    non_audio_file.write_text("not music")
    assert scan_file(non_audio_file) is None

    # TODO: This test would need a real audio file.
    # For a true unit test, you would "mock" the mutagen.File object.
    # This is a placeholder for now.
    # real_song = scan_file(Path("real_song.mp3"))
    # assert isinstance(real_song, Song)