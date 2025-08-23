# ChipiChipi
**A personal, local music manager and sync tool for music enthusiasts who want granular control over their offline music library and device syncing, without cloud subscriptions.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Status](https://img.shields.io/badge/status-alpha-orange)

> **⚠️ Notice: This project is under heavy development.**
> It is not yet feature-complete and is primarily a learning vehicle for me. Expect breaking changes, bugs, and missing features. Contributions and ideas are welcome!

## 🗺️ Planned Features / Roadmap

The goal is to build a fully-featured desktop music manager, implemented in distinct phases:

### Phase 1: The Core Library (In Progress)
*   **Library Scanner:** Recursively scan directories for audio files and import them into a local database.
*   **Metadata Reading:** Extract ID3 tags (artist, album, title, track number, etc.) using `mutagen`.
*   **Basic GUI:** A simple interface to browse the scanned music library.

### Phase 2: Playlist & Playback
*   **Playlist Management:** Create, edit, and delete playlists.
*   **Audio Playback:** Basic play, pause, skip, and seek functionality within the application.

### Phase 3: Management & Sync
*   **Metadata Editing:** Edit tags directly within the app and write them back to the audio files.
*   **Device Sync:** Intelligently sync playlists and libraries to external devices (e.g., Android phones, USB drives).

### Phase 4: Polish & Advanced Features
*   **Smart Duplicate Detection:** Find and manage duplicate tracks.
*   **Library Statistics:** View stats about your collection (total playtime, top genres, etc.).
*   **Themes & Customization:** Support for different UI themes.
