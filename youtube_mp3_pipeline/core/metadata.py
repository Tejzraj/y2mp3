"""
Metadata embedding module for MP3 files using mutagen.
Handles ID3 tags including Title, Artist, Album, and embedded Cover Art (APIC).
"""

import logging
from pathlib import Path
from typing import Optional

try:
    from mutagen.id3 import (
        ID3,
        APIC,
        ID3NoHeaderError,
        TALB,
        TIT2,
        TPE1,
    )
    from mutagen.mp3 import MP3
except ImportError:  # pragma: no cover
    ID3 = None  # type: ignore
    APIC = None  # type: ignore
    ID3NoHeaderError = Exception  # type: ignore
    TALB = None  # type: ignore
    TIT2 = None  # type: ignore
    TPE1 = None  # type: ignore
    MP3 = None  # type: ignore

logger = logging.getLogger(__name__)


def embed_id3_metadata(
    mp3_path: Path,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    album: Optional[str] = None,
    thumbnail_path: Optional[Path] = None,
    remove_thumbnail_file: bool = True,
) -> bool:
    """
    Embed ID3 tags (Title, Artist, Album, Album Art) into a target MP3 file.

    Args:
        mp3_path: Absolute or relative path to the MP3 file.
        title: Track title to set (TIT2).
        artist: Track artist/uploader to set (TPE1).
        album: Album name to set (TALB).
        thumbnail_path: Optional path to an image file (JPEG, PNG, WEBP) to embed.
        remove_thumbnail_file: If True and thumbnail was embedded, deletes the standalone image file.

    Returns:
        bool: True if metadata was successfully embedded, False otherwise.
    """
    mp3_path = Path(mp3_path)
    if not mp3_path.is_file():
        logger.error(f"Cannot embed metadata: MP3 file not found at '{mp3_path}'")
        return False

    if ID3 is None:
        logger.error("Mutagen package is not installed. Skipping ID3 metadata embedding.")
        return False

    try:
        # Load existing ID3 tag or create a new header if absent
        try:
            tags = ID3(str(mp3_path))
        except ID3NoHeaderError:
            tags = ID3()

        # Set Title (TIT2)
        if title:
            tags.setall("TIT2", [TIT2(encoding=3, text=title)])

        # Set Artist (TPE1)
        if artist:
            tags.setall("TPE1", [TPE1(encoding=3, text=artist)])

        # Set Album (TALB)
        if album:
            tags.setall("TALB", [TALB(encoding=3, text=album)])

        # Embed Album Art (APIC)
        if thumbnail_path:
            thumb_path = Path(thumbnail_path)
            if thumb_path.is_file():
                mime_type = "image/jpeg"
                suffix = thumb_path.suffix.lower()
                if suffix == ".png":
                    mime_type = "image/png"
                elif suffix == ".webp":
                    mime_type = "image/webp"

                with open(thumb_path, "rb") as img_file:
                    image_data = img_file.read()

                tags.setall(
                    "APIC",
                    [
                        APIC(
                            encoding=3,  # UTF-8
                            mime=mime_type,
                            type=3,  # 3 is front cover
                            desc="Front Cover",
                            data=image_data,
                        )
                    ],
                )

                if remove_thumbnail_file:
                    try:
                        thumb_path.unlink()
                        logger.debug(f"Removed temporary thumbnail file: {thumb_path}")
                    except OSError as e:
                        logger.warning(f"Could not remove thumbnail file {thumb_path}: {e}")

        # Save ID3 tags back to MP3
        tags.save(str(mp3_path), v2_version=3)
        logger.info(f"Successfully embedded ID3 metadata into '{mp3_path.name}'")
        return True

    except Exception as exc:
        logger.error(f"Failed to embed metadata into '{mp3_path}': {exc}", exc_info=True)
        return False
