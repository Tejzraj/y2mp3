"""
Core downloader engine using yt-dlp.
Handles sequential batch downloads of YouTube audio, conversion to MP3,
and error handling for network, ffmpeg, or invalid URLs.
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
class DownloadResult:
    """Represents the outcome of a single video download operation."""

    url: str
    success: bool
    title: Optional[str] = None
    file_path: Optional[Path] = None
    error_message: Optional[str] = None


@dataclass
class BatchSummary:
    """Represents the aggregate results of a batch download run."""

    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: List[DownloadResult] = field(default_factory=list)


class YouTubeBatchDownloader:
    """
    Orchestrates batch downloading and MP3 conversion of YouTube audio streams.
    """

    def __init__(
        self,
        download_dir: Optional[Path] = None,
        custom_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize the downloader with target directory and yt-dlp options.

        Args:
            download_dir: Target folder for saving MP3 files. Defaults to config settings.
            custom_options: Optional yt-dlp parameters to override defaults.
        """
        self.download_dir = Path(download_dir or DOWNLOAD_DIR)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Merge base options with any caller-specified overrides
        self.base_options = get_ytdl_options(download_dir=self.download_dir)
        if custom_options:
            self.base_options.update(custom_options)

    @staticmethod
    def is_ffmpeg_available() -> bool:
        """Check whether ffmpeg executable is present in the system PATH."""
        return shutil.which("ffmpeg") is not None

    @staticmethod
    def load_urls_from_file(file_path: Path) -> List[str]:
        """
        Read URLs from a text file, stripping whitespace and skipping blank or comment lines.

        Args:
            file_path: Path to the links.txt file.

        Returns:
            List[str]: Cleaned list of URL strings.
        """
        path = Path(file_path)
        if not path.is_file():
            logger.error(f"Links file not found: '{path}'")
            return []

        urls: List[str] = []
        with open(path, "r", encoding="utf-8") as f:
            for line_no, raw_line in enumerate(f, start=1):
                line = raw_line.strip()
                # Skip empty lines and comment lines
                if not line or line.startswith("#"):
                    continue
                urls.append(line)

        logger.info(f"Loaded {len(urls)} valid URL(s) from '{path.name}'")
        return urls

    def download_single(self, url: str) -> DownloadResult:
        """
        Download and convert a single YouTube URL to MP3 with embedded metadata.

        Args:
            url: YouTube video URL.

        Returns:
            DownloadResult: Object detailing the success/failure status and file info.
        """
        logger.info(f"Initiating processing for URL: {url}")

        if not self.is_ffmpeg_available():
            err = (
                "FFmpeg is not installed or not found in system PATH. "
                "Audio extraction to MP3 requires FFmpeg."
            )
            logger.error(err)
            return DownloadResult(url=url, success=False, error_message=err)

        if yt_dlp is None:
            err = "yt-dlp is not installed in the current Python environment."
            logger.error(err)
            return DownloadResult(url=url, success=False, error_message=err)

        try:
            with yt_dlp.YoutubeDL(self.base_options) as ydl:
                # Extract metadata and perform download
                info_dict = ydl.extract_info(url, download=True)
                if not info_dict:
                    return DownloadResult(
                        url=url,
                        success=False,
                        error_message="Could not extract video metadata.",
                    )

                # Resolve extracted information
                title = info_dict.get("title", "Unknown Title")
                artist = (
                    info_dict.get("artist")
                    or info_dict.get("uploader")
                    or info_dict.get("channel")
                    or "Unknown Artist"
                )
                album = info_dict.get("album") or "YouTube Downloads"

                # Find generated MP3 file
                expected_filename = ydl.prepare_filename(info_dict)
                expected_path = Path(expected_filename)
                mp3_path = expected_path.with_suffix(".mp3")

                # If outtmpl formatting created the file directly
                if not mp3_path.is_file():
                    # Check if matching MP3 file exists in download folder
                    candidates = list(self.download_dir.glob(f"*{mp3_path.stem}*.mp3"))
                    if candidates:
                        mp3_path = candidates[0]

                # Identify thumbnail file if downloaded
                thumbnail_path = None
                for ext in [".jpg", ".jpeg", ".webp", ".png"]:
                    thumb_candidate = expected_path.with_suffix(ext)
                    if thumb_candidate.is_file():
                        thumbnail_path = thumb_candidate
                        break

                # Embed ID3 tags into the resulting MP3
                if mp3_path.is_file():
                    embed_id3_metadata(
                        mp3_path=mp3_path,
                        title=title,
                        artist=artist,
                        album=album,
                        thumbnail_path=thumbnail_path,
                    )
                    logger.info(f"Successfully processed: '{title}' -> {mp3_path.name}")
                    return DownloadResult(
                        url=url,
                        success=True,
                        title=title,
                        file_path=mp3_path,
                    )
                else:
                    err = f"MP3 output file not found at expected location: {mp3_path}"
                    logger.error(err)
                    return DownloadResult(url=url, success=False, error_message=err)

        except DownloadError as de:
            error_msg = f"Download error: {str(de).strip()}"
            logger.error(f"Failed to process '{url}': {error_msg}")
            return DownloadResult(url=url, success=False, error_message=error_msg)
        except PostProcessingError as pe:
            error_msg = f"Post-processing error (FFmpeg conversion): {str(pe).strip()}"
            logger.error(f"Failed to convert '{url}': {error_msg}")
            return DownloadResult(url=url, success=False, error_message=error_msg)
        except Exception as exc:
            error_msg = f"Unexpected error: {str(exc)}"
            logger.exception(f"Unexpected exception while processing '{url}': {exc}")
            return DownloadResult(url=url, success=False, error_message=error_msg)

    def process_batch(
        self,
        links_file: Optional[Path] = None,
        urls: Optional[List[str]] = None,
    ) -> BatchSummary:
        """
        Process a list of URLs sequentially from file or direct list.

        Args:
            links_file: Optional path to links.txt. Defaults to configured LINKS_FILE.
            urls: Optional list of URLs. If provided, overrides links_file.

        Returns:
            BatchSummary: Aggregated results of the entire batch execution.
        """
        target_urls = urls
        if target_urls is None:
            target_urls = self.load_urls_from_file(links_file or LINKS_FILE)

        summary = BatchSummary(total=len(target_urls))

        for idx, url in enumerate(target_urls, start=1):
            logger.info(f"[{idx}/{summary.total}] Processing: {url}")
            result = self.download_single(url)
            summary.results.append(result)
            if result.success:
                summary.succeeded += 1
            else:
                summary.failed += 1

        logger.info(
            f"Batch completed: Total={summary.total}, "
            f"Succeeded={summary.succeeded}, Failed={summary.failed}"
        )
        return summary
