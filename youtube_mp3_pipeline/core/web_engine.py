"""
Web Automation Engine for flagaflaga.pl using Playwright.
Navigates the web converter, pastes URLs, suppresses ad popups,
waits for conversion, and downloads MP3 files directly into the downloads folder.
"""

import logging
from pathlib import Path
import time
from typing import List, Optional

try:
    from playwright.sync_api import (
        Browser,
        BrowserContext,
        Page,
        TimeoutError as PlaywrightTimeoutError,
        sync_playwright,
    )
    PLAYWRIGHT_AVAILABLE = True
except ImportError:  # pragma: no cover
    PLAYWRIGHT_AVAILABLE = False
    Browser = None  # type: ignore
    BrowserContext = None  # type: ignore
    Page = None  # type: ignore
    PlaywrightTimeoutError = Exception  # type: ignore
    sync_playwright = None  # type: ignore

from config.settings import (
    DOWNLOAD_DIR,
    FLAGA_BASE_URL,
    LINKS_FILE,
    WEB_ENGINE_HEADLESS,
    WEB_ENGINE_TIMEOUT_MS,
)
from core.direct_engine import BatchSummary, EngineResult

logger = logging.getLogger(__name__)


class WebFlagaEngine:
    """
    Fallback web automation engine targeting https://flagaflaga.pl/ via Playwright.
    """

    def __init__(
        self,
        download_dir: Optional[Path] = None,
        base_url: str = FLAGA_BASE_URL,
        headless: bool = WEB_ENGINE_HEADLESS,
        timeout_ms: int = WEB_ENGINE_TIMEOUT_MS,
    ) -> None:
        """
        Initialize WebFlagaEngine.

        Args:
            download_dir: Target directory for saved MP3s.
            base_url: The online converter URL.
            headless: Whether to run Playwright in headless mode.
            timeout_ms: Maximum wait timeout per conversion in milliseconds.
        """
        self.download_dir = Path(download_dir or DOWNLOAD_DIR)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url
        self.headless = headless
        self.timeout_ms = timeout_ms

    @staticmethod
    def is_playwright_installed() -> bool:
        """Check if Playwright Python library is available."""
        return PLAYWRIGHT_AVAILABLE

    @staticmethod
    def load_urls_from_file(file_path: Path) -> List[str]:
        """
        Read URLs from file, filtering empty lines and comments.

        Args:
            file_path: Path to links.txt.

        Returns:
            List[str]: List of valid URLs.
        """
        path = Path(file_path)
        if not path.is_file():
            logger.error(f"Links file not found: '{path}'")
            return []

        urls: List[str] = []
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                urls.append(line)

        return urls

    def _setup_ad_interceptor(self, context: BrowserContext, main_page: Page) -> None:
        """
        Configure event listeners to intercept and dismiss ad popups and new tabs.

        Args:
            context: The Playwright browser context.
            main_page: The active main converter page.
        """

        def handle_new_page(popup: Page) -> None:
            # If a new window/tab is spawned that is not our main converter, close it
            try:
                popup.wait_for_load_state(timeout=3000)
            except Exception:
                pass

            popup_url = popup.url
            if popup != main_page:
                logger.info(f"[Web Engine] Ad popup detected and closed: {popup_url}")
                try:
                    popup.close()
                except Exception as e:
                    logger.debug(f"Error closing popup: {e}")

        context.on("page", handle_new_page)

    def download_single(self, url: str) -> EngineResult:
        """
        Convert and download a single YouTube video using flagaflaga.pl automation.

        Args:
            url: YouTube video URL.

        Returns:
            EngineResult: The outcome of the download attempt.
        """
        logger.info(f"[Web Engine] Navigating flagaflaga.pl for URL: {url}")

        if not self.is_playwright_installed():
            err = (
                "Playwright is not installed. Please run:\n"
                "pip install playwright && playwright install chromium"
            )
            logger.error(err)
            return EngineResult(url=url, success=False, error_message=err)

        try:
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(
                        headless=self.headless,
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                        ],
                    )
                except Exception as browser_err:
                    err = (
                        f"Failed to launch Chromium: {browser_err}. "
                        "Ensure browsers are installed via: 'playwright install chromium'"
                    )
                    logger.error(err)
                    return EngineResult(url=url, success=False, error_message=err)

                context = browser.new_context(
                    accept_downloads=True,
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                )

                page = context.new_page()
                self._setup_ad_interceptor(context, page)

                # 1. Navigate to flagaflaga.pl
                page.goto(self.base_url, timeout=self.timeout_ms, wait_until="domcontentloaded")

                # 2. Locate link input box
                input_selector = 'input[placeholder*="Paste link"], form input[type="text"], input[x-model="query"]'
                page.wait_for_selector(input_selector, timeout=15000)
                page.fill(input_selector, url)
                logger.info("[Web Engine] URL entered into input field.")

                # 3. Click the Start / Convert button
                submit_button_selector = 'form button[type="submit"], button:has-text("Start")'
                page.wait_for_selector(submit_button_selector, timeout=10000)
                page.click(submit_button_selector)
                logger.info("[Web Engine] Conversion initiated. Waiting for download button...")

                # 4. Wait for conversion to finish and download button to appear
                # flagaflaga renders a download button or direct link once HTMX conversion resolves
                download_selectors = [
                    'a:has-text("Download")',
                    'button:has-text("Download")',
                    'a[href*="download"]',
                    'a[download]',
                    '.btn-download',
                    'a.download-btn',
                ]
                combined_selector = ", ".join(download_selectors)

                # Poll for the download element to become visible
                download_element = page.wait_for_selector(
                    combined_selector,
                    state="visible",
                    timeout=self.timeout_ms,
                )

                if not download_element:
                    err = "Conversion timed out or download button was not rendered."
                    logger.error(f"[Web Engine] {err}")
                    browser.close()
                    return EngineResult(url=url, success=False, error_message=err)

                # 5. Intercept download file event
                logger.info("[Web Engine] Download button available. Triggering file download...")
                with page.expect_download(timeout=self.timeout_ms) as download_info:
                    # Some sites require a force click to bypass invisible ad overlays
                    download_element.click(force=True)

                download = download_info.value
                filename = download.suggested_filename or f"yt_audio_{int(time.time())}.mp3"
                if not filename.endswith(".mp3"):
                    filename = f"{Path(filename).stem}.mp3"

                dest_path = self.download_dir / filename
                download.save_as(str(dest_path))

                browser.close()
                logger.info(f"[Web Engine] Successfully saved MP3: {dest_path.name}")
                return EngineResult(
                    url=url,
                    success=True,
                    title=dest_path.stem,
                    file_path=dest_path,
                )

        except PlaywrightTimeoutError:
            err = f"Operation timed out after {self.timeout_ms // 1000}s waiting for site response."
            logger.error(f"[Web Engine] {err}")
            return EngineResult(url=url, success=False, error_message=err)
        except Exception as exc:
            err = f"Web automation error: {str(exc)}"
            logger.exception(f"[Web Engine] Exception for '{url}': {exc}")
            return EngineResult(url=url, success=False, error_message=err)

    def process_batch(
        self,
        links_file: Optional[Path] = None,
        urls: Optional[List[str]] = None,
    ) -> BatchSummary:
        """
        Process links sequentially using the web automation engine.

        Args:
            links_file: Optional path to links.txt.
            urls: Optional list of URLs to process.

        Returns:
            BatchSummary: Aggregate results.
        """
        target_urls = urls
        if target_urls is None:
            target_urls = self.load_urls_from_file(links_file or LINKS_FILE)

        summary = BatchSummary(engine_name="Web Flaga (Playwright)", total=len(target_urls))

        for idx, url in enumerate(target_urls, start=1):
            logger.info(f"[{idx}/{summary.total}] [Web Engine] Processing: {url}")
            result = self.download_single(url)
            summary.results.append(result)
            if result.success:
                summary.succeeded += 1
            else:
                summary.failed += 1

        return summary
