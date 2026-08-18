"""
fetcher.py
----------
Fetches a page (rendering JS via Playwright, since a lot of university
sites build their faculty grids client-side) and strips it down to
clean text + a link list so we don't burn tokens sending raw HTML/CSS/JS
to Claude.
"""

import re
import time
import urllib.robotparser as robotparser
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

USER_AGENT = "FacultyDataResearchBot/1.0 (+contact: you@yourdomain.edu)"


def robots_allowed(url: str, user_agent: str = USER_AGENT) -> bool:
    """Best-effort robots.txt check. Defaults to True (allowed) if the
    robots.txt can't be fetched or parsed -- but you should still eyeball
    each target site's ToS yourself before scraping it at scale."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True


class Fetcher:
    def __init__(self, headless: bool = True, delay_seconds: float = 2.0, respect_robots: bool = True):
        self.delay_seconds = delay_seconds
        self.respect_robots = respect_robots
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=headless)
        self.context = self.browser.new_context(user_agent=USER_AGENT)

    def close(self):
        self.context.close()
        self.browser.close()
        self._pw.stop()

    def fetch(self, url: str, wait_ms: int = 1500) -> dict:
        """Returns {"url": ..., "text": cleaned visible text, "links": [{"text","href"}]}"""
        if self.respect_robots and not robots_allowed(url):
            raise PermissionError(f"robots.txt disallows fetching: {url}")

        page = self.context.new_page()
        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(wait_ms)  # let JS-rendered grids populate
            html = page.content()
        finally:
            page.close()

        time.sleep(self.delay_seconds)  # be polite, don't hammer the server
        return self._clean(html, url)

    @staticmethod
    def _clean(html: str, base_url: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()

        links = []
        seen_hrefs = set()

        # 1. Normal <a href="..."> links.
        for a in soup.find_all("a", href=True):
            href = urljoin(base_url, a["href"])
            if href.startswith("http") and href not in seen_hrefs:
                links.append({"text": a.get_text(strip=True), "href": href})
                seen_hrefs.add(href)

        # 2. Many university sites don't use real <a href> for faculty cards --
        # they navigate via JS (onclick="location.href='...'", data-href, etc).
        # Sweep every tag's attributes for anything URL-shaped so we don't miss
        # these. This over-collects a bit, but the LLM classification step
        # filters out anything irrelevant.
        url_like = re.compile(
            r"""['"]([^'"]*(?:\.php|\.aspx|\.html?|uname=|id=|profile)[^'"]*)['"]""",
            re.IGNORECASE,
        )
        js_attrs = ("onclick", "data-href", "data-url", "data-link", "data-uname", "data-profile")
        for tag in soup.find_all(True):
            link_text = tag.get_text(strip=True)[:80]
            for attr in js_attrs:
                val = tag.get(attr)
                if not val:
                    continue
                candidates = url_like.findall(val) or ([val] if attr != "onclick" else [])
                for cand in candidates:
                    if not cand or cand.startswith(("javascript:", "#")):
                        continue
                    href = urljoin(base_url, cand)
                    if href.startswith("http") and href not in seen_hrefs:
                        links.append({"text": link_text, "href": href})
                        seen_hrefs.add(href)

        text = soup.get_text(separator="\n", strip=True)
        # collapse excessive blank lines
        lines = [l for l in text.split("\n") if l.strip()]
        text = "\n".join(lines)

        return {"url": base_url, "text": text, "links": links}
