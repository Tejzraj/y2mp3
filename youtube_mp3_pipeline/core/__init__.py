"""Core package for YouTube MP3 Downloader Pipeline."""
from .direct_engine import (
    BatchSummary,
    DirectYtdlpEngine,
    EngineResult,
)
from .metadata import embed_id3_metadata
from .web_engine import WebFlagaEngine

# Backward-compatible alias
YouTubeBatchDownloader = DirectYtdlpEngine
DownloadResult = EngineResult

__all__ = [
    "BatchSummary",
    "DirectYtdlpEngine",
    "DownloadResult",
    "EngineResult",
    "WebFlagaEngine",
    "YouTubeBatchDownloader",
    "embed_id3_metadata",
]
