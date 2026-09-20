"""
CLI entry point for the YouTube MP3 Downloader Pipeline.
Supports dual-engine execution:
  - Direct yt-dlp Engine (default)
  - Fallback Web Automation Engine for flagaflaga.pl (Playwright)
"""

import argparse
import logging
from pathlib import Path
import sys

try:
    from colorama import Back, Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
except ImportError:
    class _ColorDummy:
        def __getattr__(self, name: str) -> str:
            return ""

    Fore = _ColorDummy()  # type: ignore
    Back = _ColorDummy()  # type: ignore
    Style = _ColorDummy()  # type: ignore

from config.settings import (
    DEFAULT_ENGINE,
    DOWNLOAD_DIR,
    LINKS_FILE,
    LOG_DIR,
    LOG_FILE,
)
from core.direct_engine import DirectYtdlpEngine
from core.web_engine import WebFlagaEngine


def setup_logging(log_file: Path) -> logging.Logger:
    """
    Configure file-based logging for the execution pipeline.

    Args:
        log_file: Path to destination log file.

    Returns:
        logging.Logger: Root logger.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def initialize_directories() -> None:
    """Ensure storage and logs directories exist on the filesystem."""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if not LINKS_FILE.exists():
        LINKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        LINKS_FILE.write_text("# Add one YouTube URL per line\n", encoding="utf-8")


def print_banner(engine_name: str) -> None:
    """Display CLI styled banner."""
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 70}")
    print(f"{Fore.CYAN}{Style.BRIGHT}         YOUTUBE MP3 BATCH DOWNLOADER PIPELINE")
    print(f"{Fore.WHITE}         Active Engine: {Fore.YELLOW}{engine_name.upper()}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 70}{Style.RESET_ALL}")


def main() -> int:
    """
    Main CLI function with argument parsing and execution flow.

    Returns:
        int: Exit status code (0 for success, 1 for errors).
    """
    parser = argparse.ArgumentParser(
        description="Batch download YouTube audio and convert to MP3."
    )
    parser.add_argument(
        "--engine",
        "-e",
        choices=["direct", "web"],
        default=DEFAULT_ENGINE,
        help="Download engine: 'direct' (yt-dlp, default) or 'web' (flagaflaga.pl automation)",
    )
    parser.add_argument(
        "--links",
        "-l",
        type=Path,
        default=LINKS_FILE,
        help=f"Path to input text file with links (default: {LINKS_FILE})",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DOWNLOAD_DIR,
        help=f"Target output directory for MP3 files (default: {DOWNLOAD_DIR})",
    )
    args = parser.parse_args()

    initialize_directories()
    logger = setup_logging(LOG_FILE)
    print_banner(args.engine)

    # Instantiate selected engine
    if args.engine == "direct":
        engine = DirectYtdlpEngine(download_dir=args.output)
        if not engine.is_ffmpeg_available():
            print(f"{Fore.RED}{Style.BRIGHT}[!] PREREQUISITE ERROR: 'ffmpeg' not found in system PATH.")
            print(
                f"{Fore.YELLOW}    Direct MP3 conversion requires FFmpeg:\n"
                f"    - macOS:   brew install ffmpeg\n"
                f"    - Windows: winget install Gyan.FFmpeg\n"
                f"    - Linux:   sudo apt-get install -y ffmpeg\n"
            )
            logger.error("Aborted: FFmpeg missing for direct engine.")
            return 1
    else:
        engine = WebFlagaEngine(download_dir=args.output)
        if not engine.is_playwright_installed():
            print(f"{Fore.RED}{Style.BRIGHT}[!] PREREQUISITE ERROR: 'playwright' is not installed.")
            print(
                f"{Fore.YELLOW}    Please install dependencies:\n"
                f"    pip install playwright && playwright install chromium\n"
            )
            logger.error("Aborted: Playwright missing for web engine.")
            return 1

    # Load input URLs
    print(f"{Fore.BLUE}[*] Reading links from: {args.links}")
    urls = engine.load_urls_from_file(args.links)
    if not urls:
        print(f"{Fore.YELLOW}[!] No URLs found in '{args.links}'. Add links to file and rerun.")
        return 0

    print(f"{Fore.GREEN}[*] Found {len(urls)} link(s) to process.")
    print(f"{Fore.BLUE}[*] Target output: {args.output.resolve()}\n")

    # Sequential execution with real-time status output
    total = len(urls)
    succeeded = 0
    failed = 0
    results = []

    for idx, url in enumerate(urls, start=1):
        progress_prefix = f"[{idx}/{total}]"
        print(f"{Fore.CYAN}{progress_prefix} {Fore.WHITE}Processing: {url}")

        result = engine.download_single(url)
        results.append(result)

        if result.success:
            succeeded += 1
            print(f"       {Fore.GREEN}✓ Success: {result.title or result.file_path.name}{Style.RESET_ALL}")
        else:
            failed += 1
            print(f"       {Fore.RED}✗ Failed: {result.error_message}{Style.RESET_ALL}")
        print()

    # Final execution summary
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 70}")
    print(f"{Fore.CYAN}{Style.BRIGHT}                        EXECUTION SUMMARY")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 70}{Style.RESET_ALL}")
    print(f"Engine Used             : {args.engine.upper()}")
    print(f"Total links processed   : {total}")
    print(f"{Fore.GREEN}Successfully downloaded : {succeeded}{Style.RESET_ALL}")
    print(f"{Fore.RED if failed > 0 else Fore.WHITE}Failed downloads        : {failed}{Style.RESET_ALL}")
    print(f"Output Directory        : {args.output.resolve()}")
    print(f"Log File Location       : {LOG_FILE.resolve()}")

    if failed > 0:
        print(f"\n{Fore.RED}{Style.BRIGHT}Failed Items Detail:{Style.RESET_ALL}")
        for r in results:
            if not r.success:
                print(f"  {Fore.RED}- {r.url}: {r.error_message}{Style.RESET_ALL}")
        return 1

    print(f"\n{Fore.GREEN}{Style.BRIGHT}[✓] All links completed successfully!{Style.RESET_ALL}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
