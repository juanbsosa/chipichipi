import pytest
from pathlib import Path
from chipichipi.scanner import parse_artist_title_from_filename

def test_parse_artist_title_from_filename():
    """Test various filename patterns for artist-title parsing."""
    
    test_cases = [
        # (filename, expected_artist, expected_title)
        ("Artist - Song Name.mp3", "Artist", "Song Name"),
        ("Artist – Song Name.mp3", "Artist", "Song Name"),  # en dash
        ("Artist---Song Name.mp3", "Artist", "Song Name"),  # multiple dashes
        ("Artist_Song Name.mp3", "Artist", "Song Name"),    # underscore
        ("Artist - Song Name (Remix).mp3", "Artist", "Song Name (Remix)"),
        ("Artist - Song Name [Official Video].mp3", "Artist", "Song Name [Official Video]"),
        ("Some Artist - Some Song feat. Other Artist.mp3", "Some Artist", "Some Song feat. Other Artist"),
        ("Artist - Song Name - Extra Info.mp3", "Artist", "Song Name - Extra Info"),
    ]
    
    for filename, expected_artist, expected_title in test_cases:
        artist, title = parse_artist_title_from_filename(filename)
        assert artist == expected_artist, f"Failed for {filename}: got {artist}, expected {expected_artist}"
        assert title == expected_title, f"Failed for {filename}: got {title}, expected {expected_title}"

def test_parse_invalid_filenames():
    """Test filenames that shouldn't be parsed."""
    
    invalid_cases = [
        "Song Name Only.mp3",
        "Artist.mp3",
        "Just a string without pattern.mp3",
        "12345.mp3",
    ]
    
    for filename in invalid_cases:
        artist, title = parse_artist_title_from_filename(filename)
        assert artist is None, f"Should not parse artist from {filename}"
        assert title is None, f"Should not parse title from {filename}"

def test_preserve_original_metadata_when_available():
    """Test that original metadata is preserved when available."""
    # This would be tested in integration tests with actual files
    pass