import pygame
import sys
from pathlib import Path

pygame.mixer.init()
test_files = [
    'test_library/Hart & Neenan - POV (Mikhu Remix).mp3',
    'test_library/Fort Romeau - Secrets & Lies.mp3',
    'test_library/Channel Tres - Top Down.mp3',
    'test_library/Beethoven - Moonlight Sonata 3er Movimiento.mp3'
]

for file_path in test_files:
    path = Path(file_path)
    if path.exists():
        try:
            pygame.mixer.music.load(str(path))
            print(f'✓ Successfully loaded: {path.name}')
        except Exception as e:
            print(f'✗ Failed to load {path.name}: {e}')
    else:
        print(f'File not found: {file_path}')