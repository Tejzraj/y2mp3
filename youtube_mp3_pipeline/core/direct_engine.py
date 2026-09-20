"""
Direct yt-dlp Engine for high-speed YouTube audio extraction.
Extracts audio streams directly from source servers, converts to MP3 via FFmpeg,
embeds metadata and cover art, and handles errors cleanly.
"""

from dataclasses import dataclass, field
import logging
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional

try:
    import yt_dlp
    from yt_dlp.utils import DownloadError, PostProcessingError
except ImportError:  # pragma: no cover
    yt_dlp = None  # type: ignore
    DownloadError = Exception  # type: ignore
    PostProcessingError = Exception  # type: ignore

from config.settings import (
    DOWNLOAD_DIR,
    LINKS_FILE,
    get_ytdl_options,
)
from core.metadata import embed_id3_metadata

logger = logging.getLogger(__name__)


@dataclass
class EngineResult:
    """Represents the outcome of a single video download operation."""

    url: str
    success: bool
    title: Optional[str] = None
    file_path: Optional[Path] = None
    error_message: Optional[str] = None


@dataclass
class BatchSummary:
    """Represents aggregate results of a batch processing execution."""

    engine_name: str
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: List[EngineResult] = field(default_factory=list)


class DirectYtdlpEngine:
    """
    Primary engine using yt-dlp to download and convert YouTube audio directly to MP3.
    """

    def __init__(
        self,
        download_dir: Optional[Path] = None,
        custom_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize the Direct yt-dlp engine.

        Args:
            download_dir: Target folder for saving MP3 files.
            custom_options: Optional overrides for yt-dlp parameters.
        """
        self.download_dir = Path(download_dir or DOWNLOAD_DIR)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.options = get_ytdl_options(download_dir=self.download_dir)
        if custom_options:
            self.options.update(custom_options)

    @staticmethod
    def is_ffmpeg_available() -> bool:
        """Check whether ffmpeg executable is present in system PATH."""
        return shutil.which("ffmpeg") is not None

    @staticmethod
    def load_urls_from_file(file_path: Path) -> List[str]:
        """
        Read URLs from a text file, stripping whitespace and skipping blank or comment lines.

        Args:
            file_path: Path to the links text file.

        Returns:
            List[str]: Cleaned list of valid URL strings.
        """
        path = Path(file_path)
        if not path.is_file():
            logger.error(f"Links file not found at: '{path}'")
            return []

        urls: List[str] = []
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                urls.append(line)

        logger.info(f"Loaded {len(urls)} URL(s) from '{path.name}'")
        return urls

    def download_single(self, url: str) -> EngineResult:
        """
        Download a single video, convert audio to MP3, and embed metadata.

        Args:
            url: YouTube video URL.

        Returns:
            EngineResult: Result outcome for this item.
        """
        logger.info(f"[Direct Engine] Processing URL: {url}")

        if not self.is_ffmpeg_available():
            err = "FFmpeg is not installed or not in system PATH. Required for MP3 conversion."
            logger.error(err)
            return EngineResult(url=url, success=False, error_message=err)

        if yt_dlp is None:
            err = "yt-dlp is not installed in the current Python environment."
            logger.error(err)
            return EngineResult(url=url, success=False, error_message=err)

        try:
            with yt_dlp.YoutubeDL(self.options) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                if not info_dict:
                    return EngineResult(
                        url=url,
                        success=False,
                        error_message="Failed to retrieve video metadata from YouTube.",
                    )

                title = info_dict.get("title", "Unknown Title")
                artist = (
                    info_dict.get("artist")
                    or info_dict.get("uploader")
                    or info_dict.get("channel")
                    or "Unknown Artist"
                )
                album = info_dict.get("album") or "YouTube Downloads"

                # Locate the converted MP3 file
                expected_filename = ydl.prepare_filename(info_dict)
                expected_path = Path(expected_filename)
                mp3_path = expected_path.with_suffix(".mp3")

                if not mp3_path.is_file():
                    # Check for glob pattern match in output directory
                    candidates = list(self.download_dir.glob(f"*{mp3_path.stem}*.mp3"))
                    if candidates:
                        mp3_path = candidates[0]

                # Check for thumbnail file
                thumbnail_path = None
                for ext in [".jpg", ".jpeg", ".webp", ".png"]:
                    thumb_candidate = expected_path.with_suffix(ext)
                    if thumb_candidate.is_file():
                        thumbnail_path = thumb_candidate
                        break

                if mp3_path.is_file():
                    embed_id3_metadata(
                        mp3_path=mp3_path,
                        title=title,
                        artist=artist,
                        album=album,
                        thumbnail_path=thumbnail_path,
                    )
                    logger.info(f"[Direct Engine] Completed: '{title}' -> {mp3_path.name}")
                    return EngineResult(
                        url=url,
                        success=True,
                        title=title,
                        file_path=mp3_path,
                    )
                else:
                    err = f"MP3 output file missing: {mp3_path}"
                    logger.error(err)
                    return EngineResult(url=url, success=False, error_message=err)

        except DownloadError as de:
            err = f"Download error: {str(de).strip()}"
            logger.error(f"[Direct Engine] {err}")
            return EngineResult(url=url, success=False, error_message=err)
        except PostProcessingError as pe:
            err = f"FFmpeg post-processing error: {str(pe).strip()}"
            logger.error(f"[Direct Engine] {err}")
            return EngineResult(url=url, success=False, error_message=err)
        except Exception as exc:
            err = f"Unexpected error: {str(exc)}"
            logger.exception(f"[Direct Engine] Exception processing '{url}': {exc}")
            return EngineResult(url=url, success=False, error_message=err)

    def process_batch(
        self,
        links_file: Optional[Path] = None,
        urls: Optional[List[str]] = None,
    ) -> BatchSummary:
        """
        Process a list of YouTube URLs sequentially.

        Args:
            links_file: Optional links file path.
            urls: Optional list of URLs.

        Returns:
            BatchSummary: Aggregated batch results.
        """
        target_urls = urls
        if target_urls is None:
            target_urls = self.load_urls_from_file(links_file or LINKS_FILE)

        summary = BatchSummary(engine_name="Direct yt-dlp", total=len(target_urls))

        for idx, url in enumerate(target_urls, start=1):
            logger.info(f"[{idx}/{summary.total}] Processing: {url}")
            result = self.download_single(url)
            summary.results.append(result)
            if result.success:
                summary.succeeded += 1
            else:
                summary.failed += 1

        return summary
