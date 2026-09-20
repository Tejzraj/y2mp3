# YouTube-to-MP3 Batch Downloader Pipeline

A production-ready batch processing pipeline for downloading YouTube audio streams and converting them to high-quality MP3s with automated ID3 tag and cover art embedding.

The pipeline features **two execution engines**:
1. **Direct Engine (`yt-dlp`) [Primary]**: High-speed, downloads streams directly from YouTube, embeds metadata and front cover art, and bypasses third-party website limits.
2. **Web Automation Engine (`playwright`) [Fallback]**: Automates conversion via `https://flagaflaga.pl/` using headless Chromium, automatically intercepts and closes ad popups, waits for conversion completion, and triggers MP3 downloads.

---

## Directory Structure

```text
youtube_mp3_pipeline/
│
├── config/
│   ├── __init__.py
│   └── settings.py          # Paths, bitrates (320kbps), and engine settings
├── core/
│   ├── __init__.py          # Exports DirectYtdlpEngine & WebFlagaEngine
│   ├── direct_engine.py     # Engine 1: Direct yt-dlp processor
│   ├── web_engine.py        # Engine 2: Playwright flagaflaga.pl automation
│   └── metadata.py          # ID3 tags (Title, Artist, Album, Cover Art)
├── storage/
│   ├── downloads/           # Saved MP3 files
│   └── links.txt            # Input YouTube URLs (one per line)
├── logs/
│   └── pipeline.log         # Execution log file
├── main.py                  # CLI entry point with --engine flag
├── requirements.txt         # Project dependencies
└── README.md                # System prerequisites & usage guide
```

---

## Prerequisites

### 1. FFmpeg (Required for Direct Engine)
FFmpeg performs audio extraction and conversion to MP3 format:

- **macOS (Homebrew):**
  ```bash
  brew install ffmpeg
  ```
- **Windows:**
  ```powershell
  winget install Gyan.FFmpeg
  # or via Chocolatey:
  choco install ffmpeg
  ```
- **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt-get update && sudo apt-get install -y ffmpeg
  ```

### 2. Chromium Browser (Required for Web Engine)
Playwright requires browser binaries to automate conversion:
```bash
playwright install chromium
```

---

## Installation & Setup

1. **Navigate to the project folder:**
   ```bash
   cd youtube_mp3_pipeline
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate       # On macOS/Linux
   # or
   .\venv\Scripts\activate        # On Windows
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browser binaries (for web engine):**
   ```bash
   playwright install chromium
   ```

---

## Usage

### 1. Configure Input URLs
Add YouTube links to `storage/links.txt`. Lines starting with `#` and empty lines are skipped:

```text
https://www.youtube.com/watch?v=bM7SZ5SBzyY
https://www.youtube.com/watch?v=K4DyBUG242c
https://www.youtube.com/watch?v=J2X5mJ3HDYE
```

### 2. Run with Primary Engine (Direct `yt-dlp`)
Fastest and highest quality (320kbps MP3 with embedded cover art):
```bash
python main.py --engine direct
# or simply
python main.py
```

### 3. Run with Fallback Engine (Web Automation for flagaflaga.pl)
Uses Playwright to automate conversion through `flagaflaga.pl`:
```bash
python main.py --engine web
```

### 4. Custom Paths
Customize input links or output destination:
```bash
python main.py --engine direct --links /path/to/custom_links.txt --output /path/to/music/
```

---

## Engine Comparison

| Feature | Direct Engine (`yt-dlp`) | Web Engine (`flagaflaga.pl`) |
|---|---|---|
| **Speed** | Instant direct download | Queued web conversion |
| **Bitrate** | Up to 320 kbps (Configurable) | Web service default |
| **Metadata & Cover Art** | Auto-embedded into ID3 tags | Standard file tagging |
| **Dependencies** | `yt-dlp`, `ffmpeg`, `mutagen` | `playwright`, Chromium |
| **Ad Handling** | Not applicable (Direct API) | Automatic ad popup dismissal |
