<div align="center">

# 🎧 y2mp3

### DUAL-ENGINE AUDIO PIPELINE
**Extract • Transcode • Enrich • Export**

<br/>

[![Python](https://img.shields.io/badge/Python-3.9%2B-00D9FF?style=flat-square&logo=python&logoColor=black)](https://python.org)
[![yt-dlp](https://img.shields.io/badge/Engine-yt--dlp-FF7A00?style=flat-square&logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![Playwright](https://img.shields.io/badge/Engine-Playwright-22C55E?style=flat-square&logo=playwright&logoColor=white)](https://playwright.dev)
[![FFmpeg](https://img.shields.io/badge/Transcoder-FFmpeg-white?style=flat-square&logo=ffmpeg&logoColor=black)](https://ffmpeg.org)
[![Mutagen](https://img.shields.io/badge/Metadata-Mutagen-A855F7?style=flat-square)](https://mutagen.readthedocs.io)
[![License](https://img.shields.io/badge/License-MIT-F59E0B?style=flat-square)](LICENSE)

<br/>

> A modular Python pipeline for batch audio extraction, MP3 transcoding, and metadata enrichment.

<br/>

[Architecture](#-architecture) • [Features](#-quick-overview) • [Pipeline](#-pipeline) • [Engines](#-engines) • [Installation](#-installation) • [Usage](#-usage) • [Structure](#-project-structure)

<br/>

![y2mp3 Architecture](assets/architecture.svg)

</div>

---

## ⚡ Quick Overview

| ⚡ Core | 🛠️ Engineering |
| :--- | :--- |
| **Dual extraction engines** | **Batch URL queue** (`storage/links.txt`) |
| **Direct Engine (`yt-dlp`)** | **FFmpeg transcoding** (libmp3lame 320 kbps) |
| **Web Engine (`Playwright`)** | **Mutagen ID3 metadata** (Title, Artist, Album) |
| **Automatic cover art embedding** | **Fault-isolated structured logging** |

---

## ⚙️ Pipeline

```text
URLs (storage/links.txt)
  │
  ▼
CLI Router (main.py)
  ├── Direct Engine (yt-dlp)
  └── Web Engine (Playwright)
  │
  ▼
FFmpeg Transcoder (libmp3lame)
  │
  ▼
Metadata + Artwork (Mutagen ID3)
  │
  ▼
MP3 Output (storage/downloads/*.mp3)
```

---

## 🔀 Engines

| Capability | Direct Engine | Web Engine |
| :--- | :--- | :--- |
| **Engine** | `yt-dlp` | `Playwright` |
| **Runtime** | Native stream demuxing | Headless Chromium |
| **Transcoding** | FFmpeg post-processing | Remote conversion workflow |
| **Cover Art** | Automatic ID3 front-cover (`APIC`) | Remote file default |
| **Ad Handling** | Not applicable (Direct API) | Automatic popup dismissal |
| **Purpose** | Primary execution path | Alternate / fallback path |

---

## 📦 Installation

### 1. System Prerequisite: FFmpeg
Required by the Direct Engine for audio demuxing and MP3 transcoding:

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows (winget or choco)
winget install Gyan.FFmpeg
```

### 2. Python Environment & Dependencies

```bash
git clone https://github.com/Tejzraj/y2mp3.git
cd y2mp3

python3 -m venv venv
source venv/bin/activate        # Windows: .\venv\Scripts\activate

pip install -r youtube_mp3_pipeline/requirements.txt
playwright install chromium
```

---

## 🚀 Usage

Execute batch jobs using either the direct engine or web fallback:

```bash
# Enter project directory
cd youtube_mp3_pipeline

# Primary direct stream engine (Default)
python main.py --engine direct

# Web automation fallback engine (flagaflaga.pl)
python main.py --engine web

# Custom queue file and output directory
python main.py --engine direct --links ./storage/links.txt --output ./storage/downloads
```

### Input Queue

Add YouTube links to `storage/links.txt`:

```text
https://www.youtube.com/watch?v=bM7SZ5SBzyY
https://www.youtube.com/watch?v=K4DyBUG242c
```

> One URL per line. Lines beginning with `#` and blank lines are ignored.

---

## 📁 Project Structure

```text
y2mp3/
├── assets/                 # Vector architecture and waveform graphics
├── youtube_mp3_pipeline/
│   ├── config/             # Path constants, bitrates, and engine settings
│   ├── core/
│   │   ├── direct_engine.py# Primary engine (yt-dlp + FFmpeg stream demuxer)
│   │   ├── web_engine.py   # Fallback engine (Playwright browser automation)
│   │   └── metadata.py     # Mutagen ID3 tag & cover art mutator
│   ├── storage/
│   │   ├── links.txt       # Sequential batch URL queue
│   │   └── downloads/      # Target output folder for MP3 files
│   ├── logs/               # Persistent pipeline audit logs (pipeline.log)
│   ├── main.py             # CLI router & terminal interface
│   └── requirements.txt    # Python dependencies
├── LICENSE                 # MIT License
└── README.md               # Project documentation
```

---

## 🛠️ Tech Stack

```text
Python 3.9+
  │
  ├── yt-dlp       (Direct stream extraction)
  ├── Playwright   (Headless browser automation)
  ├── FFmpeg       (Audio demuxing & MP3 transcoding)
  ├── Mutagen      (ID3v2 metadata & artwork injection)
  └── Colorama     (Terminal formatting & status)
```

---

## ⚖️ Responsible Use

> Use `y2mp3` only with content you are authorized to download or process. Users are responsible for complying with applicable laws and platform terms of service.

---

## 🗺️ Roadmap

- [ ] Parallel batch processing with concurrency worker limits
- [ ] Automatic fallback to Web Engine on rate-limit triggers
- [ ] Duplicate detection and queue resume support
- [ ] Structured JSON logging output

---

## 📄 License

Distributed under the [MIT License](LICENSE).

---

<div align="center">

<img src="assets/waveform.svg" alt="Waveform" width="300"/>

<br/>

**🎧 y2mp3**  
*Dual-engine audio processing for developers.*  
Built with Python • yt-dlp • Playwright • FFmpeg

</div>
