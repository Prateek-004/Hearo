# ♪ Hearo v1.0 — Smart Offline Music Player

A Spotify-inspired offline music player built with Python.
No internet required — all features work 100% locally.

---

## 🚀 Quick Start

### Windows
1. Install Python 3.8+ from https://python.org  
2. Double-click **`install_and_run.bat`**

### Linux / macOS
```bash
chmod +x install_and_run.sh
./install_and_run.sh
```

### Manual
```bash
pip install -r requirements.txt
python hearo.py
```

---

## 🎵 Features

| Feature | Description |
|---------|-------------|
| **Add Songs / Folder** | Import MP3, FLAC, WAV, OGG, M4A, WMA, AAC |
| **Play / Pause** | Space bar or click |
| **Next / Previous** | ⏮ ⏭ buttons or ← → arrow keys |
| **Seek** | Click or drag the progress bar |
| **Volume** | Drag the volume bar, or ↑ ↓ keys |
| **Shuffle** | Random playback order |
| **AI Shuffle ✦** | Queues songs similar to current track (no internet!) |
| **Repeat** | Off → Repeat All → Repeat One |
| **Like Songs** | Click ♥ column or heart in player |
| **Playlists** | Create, manage, right-click to delete |
| **Search** | Real-time search by title, artist, album |
| **Sort** | Sort by Title, Artist, Album, Duration, or Date Added |
| **AI Picks** | Recommendation panel based on listening history |
| **Find Similar** | Right-click any song → "Find Similar (AI)" |
| **Album Art** | Displayed in player bar if embedded in file |

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play / Pause |
| `←` / `→` | Seek backward / forward 5s |
| `↑` / `↓` | Volume up / down |
| `N` | Next song |
| `P` | Previous song |
| `M` | Mute / Unmute |
| `S` | Toggle Shuffle |
| `R` | Cycle Repeat mode |
| `Delete` | Remove selected song from library |

---

## 🤖 How AI Shuffle Works

Hearo builds a **feature vector** for each song from:
- Genre tags
- Artist fingerprint
- Album grouping  
- Duration bucket
- Bitrate
- Decade (from year tag)

Similarity is computed using **cosine similarity** — all locally,
no cloud API, no internet connection needed.

When AI Shuffle is ON, the queue is built by selecting the most
similar songs to the current track, then gradually introducing
slightly less similar ones to keep things interesting.

---

## 📁 Data Storage

Your library, playlists, and play history are saved to:
- **Windows**: `C:\Users\<you>\.hearo\`
- **Linux/macOS**: `~/.hearo/`

---

## 🛠 Requirements

- Python 3.8+
- pygame ≥ 2.0
- mutagen ≥ 1.45 (metadata & album art)
- Pillow ≥ 9.0 (album art display)
- numpy ≥ 1.21 (faster AI similarity, optional)
