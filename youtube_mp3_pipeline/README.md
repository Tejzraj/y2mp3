```markdown
<div align="center">

# 🎧 y2mp3 — Dual-Engine Audio Extraction Pipeline

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![yt-dlp](https://img.shields.io/badge/Engine-yt--dlp-red.svg?style=for-the-badge&logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![Playwright](https://img.shields.io/badge/Engine-Playwright-green.svg?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev)
[![License](https://img.shields.io/badge/License-MIT-purple.svg?style=for-the-badge)](LICENSE)

*An ultra-fast, production-grade batch processing pipeline to download, transcode, and enrich YouTube audio with automatic metadata and high-res cover art.*

[Key Features](#-key-features) • [System Architecture](#-system-architecture) • [Prerequisites](#-prerequisites) • [Quick Start](#-quick-start) • [Usage](#-usage)

---

```text
       ___                  _____ 
  _n_ /  _ \_  _ ________  /___  /
 /_  |  // // / / __/  _ \  __/ / 
  / /  /  / /_/ / /_/  __/ /___/  
 /_/  /  /\____/___/\___/________/
     /___/                        

```

---

## ⚡ Key Features

* **🚀 Dual Execution Architecture:**
* **Direct Engine (`yt-dlp`):** Ultra-fast stream extraction straight from source servers (up to 320 kbps VBR/CBR).
* **Web Engine (`playwright`):** Headless Chromium fallback automation for `flagaflaga.pl` with dynamic ad-interception and popup suppression.


* **🏷️ Automated Metadata Enrichment:** Uses `mutagen` to inject ID3v2 tags (Title, Artist, Track Number) and embed high-resolution video thumbnails directly as MP3 album cover art.
* **📋 Batch Processing Queue:** Reads URLs sequentially from a configurable text file, skipping comments (`#`) and invalid lines without interrupting queue progress.
* **🛡️ Robust Fault Tolerance:** Integrated error logging via Python’s `logging` module and non-blocking retry handlers for dropped connections.
* **🎨 Terminal UI:** Colored, real-time download status output powered by `colorama`.

---

## 🏗️ System Architecture

```text
               ┌───────────────────────────────┐
               │    storage/links.txt (Input)   │
               └───────────────┬───────────────┘
                               │
                       ┌───────┴───────┐
                       │    main.py    │
                       └───────┬───────┘
                               │
               ┌───────────────┴───────────────┐
               │     Engine Controller Router  │
               └───────┬───────────────┬───────┘
                       │               │
       [--engine direct]               [--engine web]
                       │               │
                       ▼               ▼
           ┌────────────────┐     ┌────────────────┐
           │ Direct Engine  │     │   Web Engine   │
           │   (yt-dlp)     │     │  (Playwright)  │
           └───────┬────────┘     └───────┬────────┘
                   │                      │
                   ▼                      ▼
           ┌────────────────┐     ┌────────────────┐
           │ FFmpeg Extract │     │ flagaflaga.pl  │
           │ & MP3 Convert  │     │ Intercept Ads  │
           └───────┬────────┘     └───────┬────────┘
                   │                      │
                   └───────┬──────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │   Mutagen ID3 Tagger   │
               │ (Metadata + Artwork)   │
               └───────────┬────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │ storage/downloads/*.mp3│
               └────────────────────────┘

```

---

## ⚙️ Prerequisites

### 1. System Dependency: FFmpeg

FFmpeg is required by the **Direct Engine** for demuxing and transcoding audio streams to `.mp3`.

* **macOS:**
```bash
brew install ffmpeg

```


* **Windows (PowerShell):**
```powershell
winget install Gyan.FFmpeg

```


* **Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install -y ffmpeg

```



---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone [https://github.com/Tejzraj/y2mp3.git](https://github.com/Tejzraj/y2mp3.git)
cd y2mp3

```

### 2. Set Up Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate        # macOS/Linux
# .\venv\Scripts\activate       # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser binaries (for web engine)
playwright install chromium

```

---

## 💻 Usage

### 1. Prepare Your Links

Add YouTube video or playlist links to `storage/links.txt` (one per line):

```text
# Favorite Tracks Queue
[https://www.youtube.com/watch?v=dQw4w9WgXcQ](https://www.youtube.com/watch?v=dQw4w9WgXcQ)
[https://www.youtube.com/watch?v=3JZ_D3ELwOQ](https://www.youtube.com/watch?v=3JZ_D3ELwOQ)

```

### 2. Execute Batch Pipeline

```bash
# Run with Primary Engine (yt-dlp) — Default
python main.py --engine direct

# Run with Fallback Web Engine (flagaflaga.pl Playwright scraper)
python main.py --engine web

# Custom input file and custom output directory
python main.py --engine direct --links ./my_links.txt --output ~/Music/Downloads

```

---

## 📊 Engine Comparison

| Feature / Capability | Direct Engine (`yt-dlp`) | Web Engine (`flagaflaga.pl`) |
| --- | --- | --- |
| **Download Speed** | ⚡ Instant (Direct Stream) | ⏳ Queued Processing |
| **Max Bitrate** | 🔊 Up to 320 kbps (VBR/CBR) | 🎧 Web Default (~128-192 kbps) |
| **Cover Art Embedding** | 🖼️ High-Res Thumbnail | ❌ Basic File |
| **Ad-Block Handling** | 🛡️ Native (API Level) | 🤖 Automated Tab Interceptor |
| **Dependencies** | `yt-dlp`, `ffmpeg` | `playwright`, `chromium` |

---

## 📁 Repository Structure

```text
y2mp3/
│
├── config/
│   ├── __init__.py
│   └── settings.py         # Bitrate, audio parameters, & system paths
├── core/
│   ├── __init__.py         # Package exports
│   ├── direct_engine.py    # Direct yt-dlp stream processor
│   ├── web_engine.py       # Playwright browser scraper
│   └── metadata.py         # ID3 tag & album artwork mutator
├── storage/
│   ├── downloads/          # Output directory for transcoded MP3s
│   └── links.txt           # Batch queue list
├── logs/
│   └── pipeline.log        # Rolling logs
├── main.py                 # CLI controller entrypoint
├── requirements.txt        # Python dependency manifest
└── README.md               # Project documentation

```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

```

```
