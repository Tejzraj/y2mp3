"""
Configuration settings for the YouTube MP3 Downloader Pipeline.
Defines project paths, bitrates, default engine options, and third-party web configurations.
"""

from pathlib import Path
from typing import Any, Dict

# Base project directory
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Storage and file paths
DOWNLOAD_DIR: Path = BASE_DIR / "storage" / "downloads"
LINKS_FILE: Path = BASE_DIR / "storage" / "links.txt"
LOG_DIR: Path = BASE_DIR / "logs"
LOG_FILE: Path = LOG_DIR / "pipeline.log"

# Default engine selection ("direct" or "web")
DEFAULT_ENGINE: str = "direct"

# Default audio conversion settings
DEFAULT_AUDIO_QUALITY: str = "160"  # kbps (high quality)
DEFAULT_AUDIO_FORMAT: str = "bestaudio/best"

# Web automation engine settings (for flagaflaga.pl)
FLAGA_BASE_URL: str = "https://flagaflaga.pl/"
WEB_ENGINE_HEADLESS: bool = True
WEB_ENGINE_TIMEOUT_MS: int = 60000  # 60s max per conversion


def get_ytdl_options(
    download_dir: Path = DOWNLOAD_DIR,
    quality: str = DEFAULT_AUDIO_QUALITY,
    quiet: bool = True,
) -> Dict[str, Any]:
    """
    Generate yt-dlp configuration dictionary.

    Args:
        download_dir: Directory where downloaded MP3 files will be stored.
        quality: Preferred audio bitrate in kbps (e.g., '192', '320').
        quiet: If True, suppresses yt-dlp internal stdout logging.

    Returns:
        Dict[str, Any]: Configuration dictionary for yt_dlp.YoutubeDL.
    """
    output_template = str(download_dir / "%(title)s.%(ext)s")

    return {
        "format": DEFAULT_AUDIO_FORMAT,
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            },
            {
                "key": "FFmpegMetadata",
                "add_metadata": True,
            },
        ],
        "writethumbnail": True,
        "quiet": quiet,
        "no_warnings": True,
        "ignoreerrors": False,
        "socket_timeout": 30,
        "retries": 3,
    }


# Default global configuration instance
YTDL_DEFAULT_OPTIONS: Dict[str, Any] = get_ytdl_options()
