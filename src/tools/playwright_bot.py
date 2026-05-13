"""
Stealth Scraper — maximum speed edition.

Speed stack:
  1. Resource blocking  — images/fonts/media blocked in every Playwright page
                          (pages load 2-3x faster)
  2. aiohttp email hunt — direct HTTP requests replace browser tabs for email
                          (10-50x faster than opening a tab)
  3. Playwright fallback — only for JS-heavy sites that need a real browser
  4. 8 concurrent detail workers + 20 concurrent HTTP workers

Phase 1 : single browser, unlimited scroll until end-of-list
Phase 2 : N concurrent Playwright workers (Maps detail)
          → each fires an aiohttp request for email
          → Playwright tab fallback if aiohttp returns nothing
"""

import asyncio
import csv
import random
import re
import ssl
import os
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import unquote, urlparse

import aiohttp
from playwright.async_api import async_playwright, Page, BrowserContext

from src.config import settings
from src.models import BusinessLead

try:
    from playwright_stealth import stealth_async
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False

# ── SSL context that ignores bad certs on small business sites ─────────────
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Resource types to block in Playwright (not needed for scraping)
_BLOCK_TYPES = {"image", "media", "font", "other"}

# False-positive fragments for email regex
_EMAIL_FP = {
    "sentry.io", "example.", "domain.", "wix.", "noreply", "no-reply",
    "donotreply", "placeholder", "@2x", "@3x", "schema.org", "w3.org",
    "googleapis", "cloudflare", "bootstrap", "jquery", "webpack",
    "unpkg.com", "jsdelivr", "emailprotected", "yourname", "youremail",
    "user@", "test@", "info@example",
}
_EMAIL_BAD_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    ".ico", ".css", ".js", ".woff", ".ttf", ".otf",
}
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
_CONTACT_KW = {"kontakt", "contact", "about", "impressum", "team", "equipe", "reach"}


def _parse_email(html: str) -> str:
    """Extract first valid email from raw HTML string."""
    for e in _EMAIL_RE.findall(html):
        el = e.lower()
        if any(fp in el for fp in _EMAIL_FP):
            continue
        if any(el.endswith(x) for x in _EMAIL_BAD_EXT):
            continue
        tld = el.rsplit(".", 1)[-1]
        if tld.isdigit() or not (2 <= len(tld) <= 10):
            continue
        return e
    return "N/A"


class StealthScraperTool:
    def __init__(self):
        self._results: List[BusinessLead] = []
        self._seen_names: set = set()
        self._lock: Optional[asyncio.Lock] = None
        self._done = 0
        self._total = 0
        # Semaphores created inside event loop
        self._web_sem: Optional[asyncio.Semaphore] = None
        self._pw_fallback_sem: Optional[asyncio.Semaphore] = None

    # ──────────────────────────────────────────────────────────────
    # Entry point
    # ──────────────────────────────────────────────────────────────

    async def scrape(
        self,
        location: str,
        business_type: str,
        output_file: str = "leads_output.csv",
    ) -> List[BusinessLead]:
        self._results = []
        self._seen_names = set()
        self._done = 0
        self._lock = asyncio.Lock()
        self._web_sem = asyncio.Semaphore(settings.web_workers)
        self._pw_fallback_sem = asyncio.Semaphore(settings.playwright_fallback_workers)

        query = f"{business_type} in {location}"
        maps_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        print(f"\n  OPENING: {maps_url}")

        # Shared aiohttp session for all email HTTP requests
        connector = aiohttp.TCPConnector(ssl=_SSL_CTX, limit=settings.web_workers)
        timeout = aiohttp.ClientTimeout(total=12, connect=6)

        async with aiohttp.ClientSession(
            connector=connector, headers=_HEADERS, timeout=timeout
        ) as http_session:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=settings.headless)
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 900},
                    user_agent=_HEADERS["User-Agent"],
                    locale="en-US",
                )

                try:
                    # ── Phase 1: scroll ───────────────────────────────
                    scroll_page = await context.new_page()
                    await self._block_resources(scroll_page, block_stylesheets=False)
                    if HAS_STEALTH:
                        try:
                            await stealth_async(scroll_page)
                        except Exception:
                            pass

                    print("  NAVIGATING to Google Maps...")
                    await scroll_page.goto(maps_url, wait_until="domcontentloaded", timeout=30000)
                    await scroll_page.wait_for_timeout(4000)
                    await self._handle_consent(scroll_page)
                    await scroll_page.wait_for_timeout(2000)

                    self._init_csv(output_file)
                    card_urls = await self._scroll_and_collect_links(scroll_page)
                    await scroll_page.close()

                    self._total = len(card_urls)
                    print(
                        f"\n  FOUND {self._total} businesses. "
                        f"Extracting with {settings.detail_workers} Playwright workers "
                        f"+ {settings.web_workers} HTTP workers...\n"
                    )

                    # ── Phase 2: parallel extraction ──────────────────
                    self._print_header()
                    await self._process_batch(context, http_session, card_urls, business_type, output_file)
                    print(f"{'─'*140}")

                except Exception as e:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    try:
                        ep = await context.new_page()
                        await ep.screenshot(path=f"error_{ts}.png")
                        await ep.close()
                    except Exception:
                        pass
                    print(f"\n  ERROR: {e}")
                finally:
                    await browser.close()

        print(f"\n  DONE: {len(self._results)} leads extracted.")
        return self._results

    # ──────────────────────────────────────────────────────────────
    # Resource blocking — speeds up every page load significantly
    # ──────────────────────────────────────────────────────────────

    async def _block_resources(self, page: Page, block_stylesheets: bool = True):
        blocked = _BLOCK_TYPES | ({"stylesheet"} if block_stylesheets else set())

        async def _handler(route):
            if route.request.resource_type in blocked:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", _handler)

    # ──────────────────────────────────────────────────────────────
    # Consent popup
    # ──────────────────────────────────────────────────────────────

    async def _handle_consent(self, page: Page):
        try:
            for sel in ["button:has-text('Accept all')", "button:has-text('Reject all')"]:
                btn = page.locator(sel)
                if await btn.count() > 0:
                    await btn.first.click()
                    await page.wait_for_timeout(1500)
                    break
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────
    # Phase 1 — unlimited scroll
    # ──────────────────────────────────────────────────────────────

    async def _scroll_and_collect_links(self, page: Page) -> List[Tuple[str, str]]:
        feed_sel = 'div[role="feed"]'
        try:
            await page.wait_for_selector(feed_sel, timeout=10000)
            print("  Scrolling (no result cap — stops at end of list)...")
        except Exception:
            print("  WARNING: No feed found.")
            return []

        consecutive_empty = 0
        total_scrolls = 0
        collected: List[Tuple[str, str]] = []

        while (
            consecutive_empty < settings.max_scroll_attempts
            and total_scrolls < settings.max_total_scrolls
        ):
            await page.evaluate(f'''
                const f = document.querySelector('{feed_sel}');
                if (f) f.scrollTop = f.scrollHeight;
            ''')
            await asyncio.sleep(random.uniform(settings.scroll_delay_min, settings.scroll_delay_max))
            total_scrolls += 1

            raw = await page.evaluate('''() => {
                const links = document.querySelectorAll('a[href*="/maps/place/"]');
                return Array.from(links).map(a => [
                    a.getAttribute("aria-label") || "",
                    a.getAttribute("href") || ""
                ]);
            }''')

            new_found = 0
            for name, href in raw:
                name, href = name.strip(), href.strip()
                if name and href and name not in self._seen_names:
                    self._seen_names.add(name)
                    collected.append((name, href))
                    new_found += 1

            if new_found:
                print(f"\r  Scrolling... {len(collected)} collected", end="", flush=True)
                consecutive_empty = 0
            else:
                consecutive_empty += 1

            # End-of-list markers (multiple locales)
            for marker in [
                "You've reached the end of the list",
                "reached the end",
                "Fin de la liste",
                "Ende der Liste",
            ]:
                if await page.locator(f"text={marker}").count() > 0:
                    raw2 = await page.evaluate('''() => {
                        return Array.from(document.querySelectorAll('a[href*="/maps/place/"]'))
                            .map(a => [a.getAttribute("aria-label")||"", a.getAttribute("href")||""]);
                    }''')
                    for name, href in raw2:
                        name, href = name.strip(), href.strip()
                        if name and href and name not in self._seen_names:
                            self._seen_names.add(name)
                            collected.append((name, href))
                    print(f"\r  END OF LIST: {len(collected)} businesses.          ")
                    return collected

            if await self._is_captcha(page):
                print(f"\r  CAPTCHA after {len(collected)} businesses.     ")
                break

        reason = (
            "max_total_scrolls" if total_scrolls >= settings.max_total_scrolls
            else "no new results"
        )
        print(f"\r  STOPPED ({reason}): {len(collected)} businesses.     ")
        return collected

    # ──────────────────────────────────────────────────────────────
    # Phase 2 — N concurrent Playwright workers
    # ──────────────────────────────────────────────────────────────

    async def _process_batch(
        self,
        context: BrowserContext,
        http_session: aiohttp.ClientSession,
        card_urls: List[Tuple[str, str]],
        business_type: str,
        output_file: str,
    ):
        sem = asyncio.Semaphore(settings.detail_workers)
        in_progress: set = set()

        async def worker(idx: int, name: str, url: str):
            async with sem:
                in_progress.add(name[:30])
                print(f"  → [{idx}/{self._total}] Starting: {name[:50]}", flush=True)
                page = await context.new_page()
                await self._block_resources(page, block_stylesheets=False)
                try:
                    lead = await asyncio.wait_for(
                        self._extract_detail(page, http_session, name, url, business_type, idx),
                        timeout=60,
                    )
                    if lead:
                        async with self._lock:
                            self._results.append(lead)
                            self._done += 1
                            self._append_to_csv(output_file, [lead])
                            self._print_lead(self._done, lead)
                    else:
                        print(f"  ✗ [{idx}/{self._total}] No data: {name[:50]}", flush=True)
                except asyncio.TimeoutError:
                    print(f"  ✗ [{idx}/{self._total}] TIMEOUT: {name[:50]}", flush=True)
                except Exception as e:
                    print(f"  ✗ [{idx}/{self._total}] ERROR: {name[:50]} — {e}", flush=True)
                finally:
                    in_progress.discard(name[:30])
                    try:
                        await page.close()
                    except Exception:
                        pass

        await asyncio.gather(
            *[asyncio.create_task(worker(i + 1, n, u)) for i, (n, u) in enumerate(card_urls)],
            return_exceptions=True,
        )

    # ──────────────────────────────────────────────────────────────
    # Maps detail extraction
    # ──────────────────────────────────────────────────────────────

    async def _extract_detail(
        self,
        page: Page,
        http_session: aiohttp.ClientSession,
        name: str,
        url: str,
        business_type: str,
        idx: int,
    ) -> Optional[BusinessLead]:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2500)
        except Exception:
            return None

        rating, reviews = 0.0, 0
        address, phone, website = "N/A", "N/A", "N/A"
        category = business_type
        google_maps_url = url.split("?")[0]
        social_links_list: List[str] = []

        # Rating & reviews
        try:
            div = page.locator('div.F7nice')
            if await div.count() > 0:
                parts = (await div.first.inner_text()).replace("\n", " ")
                m = re.search(r'(\d+[.,]\d+)', parts)
                if m:
                    rating = float(m.group(1).replace(",", "."))
                m2 = re.search(r'\(([\d,.\s ]+)\)', parts)
                if m2:
                    s = re.sub(r'[^\d]', '', m2.group(1))
                    if s.isdigit():
                        reviews = int(s)
        except Exception:
            pass

        # Category
        try:
            cb = page.locator('button[jsaction*="category"]')
            if await cb.count() > 0:
                category = (await cb.first.inner_text()).strip()
            else:
                cs = page.locator('span.DkEaL')
                if await cs.count() > 0:
                    category = (await cs.first.inner_text()).strip()
        except Exception:
            pass

        # Website — authority href first (actual URL, not display text)
        try:
            wl = page.locator('a[data-item-id="authority"]')
            if await wl.count() > 0:
                raw = (await wl.first.get_attribute("href") or "").strip()
                if raw:
                    if "/url?q=" in raw:
                        m = re.search(r'/url\?q=([^&]+)', raw)
                        raw = unquote(m.group(1)) if m else raw
                    website = raw
        except Exception:
            pass

        # Address & phone from info rows
        try:
            items = page.locator('div.Io6YTe.fontBodyMedium')
            for i in range(await items.count()):
                try:
                    text = (await items.nth(i).inner_text()).strip()
                    if not text:
                        continue
                    parent = items.nth(i).locator("..")
                    hint = (
                        (await parent.get_attribute("aria-label") or "")
                        + " "
                        + (await parent.get_attribute("data-tooltip") or "")
                    ).lower()

                    if "address" in hint or "location" in hint:
                        address = text
                    elif "phone" in hint or "call" in hint:
                        phone = text
                    elif ("website" in hint or "site" in hint) and website == "N/A":
                        website = text
                    else:
                        cl = re.sub(r'[\s\-()+]', '', text)
                        if cl.isdigit() and len(cl) >= 8 and phone == "N/A":
                            phone = text
                        elif text.startswith("+") and phone == "N/A":
                            phone = text
                        elif len(text) > 15 and "," in text and address == "N/A":
                            address = text
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback: address
        if address == "N/A":
            try:
                el = page.locator('button[data-item-id="address"] div.Io6YTe')
                if await el.count() > 0:
                    address = (await el.first.inner_text()).strip()
            except Exception:
                pass

        # Fallback: phone
        if phone == "N/A":
            try:
                el = page.locator('button[data-tooltip="Copy phone number"] div.Io6YTe')
                if await el.count() > 0:
                    phone = (await el.first.inner_text()).strip()
            except Exception:
                pass

        # Normalize website
        if website != "N/A":
            if not website.startswith("http"):
                website = "https://" + website
            website = website.split("?")[0].rstrip("/")

        # Social links
        try:
            social_domains = [
                "facebook.com", "instagram.com", "twitter.com", "x.com",
                "linkedin.com", "youtube.com", "tiktok.com", "pinterest.com",
            ]
            all_a = page.locator('a[href]')
            for i in range(min(await all_a.count(), 60)):
                try:
                    href = (await all_a.nth(i).get_attribute("href") or "").strip()
                    if not href or not href.startswith("http"):
                        continue
                    if "/url?q=" in href:
                        m = re.search(r'/url\?q=([^&]+)', href)
                        if m:
                            href = unquote(m.group(1))
                    for d in social_domains:
                        if d in href and href not in social_links_list:
                            social_links_list.append(href)
                            break
                except Exception:
                    continue
        except Exception:
            pass

        # Email — fast HTTP first, Playwright fallback if needed
        email_address = "N/A"
        if website != "N/A":
            email_address = await self._hunt_email(http_session, page.context, website)

        return BusinessLead(
            business_name=name,
            category=category,
            address=address,
            phone_number=phone,
            email_address=email_address,
            website=website,
            rating=rating,
            total_reviews=reviews,
            google_maps_url=google_maps_url,
            social_links=", ".join(social_links_list) if social_links_list else "N/A",
        )

    # ──────────────────────────────────────────────────────────────
    # Email hunting — aiohttp first, Playwright fallback
    # ──────────────────────────────────────────────────────────────

    async def _hunt_email(
        self,
        session: aiohttp.ClientSession,
        context: BrowserContext,
        website: str,
    ) -> str:
        # ── 1. Fast HTTP path ──────────────────────────────────────
        async with self._web_sem:
            email = await self._http_email(session, website)
        if email != "N/A":
            return email

        # ── 2. Playwright fallback (JS-rendered pages) ─────────────
        async with self._pw_fallback_sem:
            email = await self._playwright_email(context, website)
        return email

    async def _http_email(self, session: aiohttp.ClientSession, website: str) -> str:
        """Fetch pages with aiohttp and scan for emails — no browser needed."""
        try:
            html = await self._fetch(session, website)
            if not html:
                return "N/A"

            # Check mailto links first
            for href in re.findall(r'href=["\']mailto:([^"\'?\s]+)', html, re.I):
                if "@" in href:
                    return href.strip()

            email = _parse_email(html)
            if email != "N/A":
                return email

            # Find contact / about links
            contact_urls: List[str] = []
            base = f"{urlparse(website).scheme}://{urlparse(website).netloc}"
            for href in re.findall(r'href=["\']([^"\'#\s]+)["\']', html, re.I):
                hl = href.lower()
                if any(kw in hl for kw in _CONTACT_KW):
                    full = href if href.startswith("http") else base + "/" + href.lstrip("/")
                    if full not in contact_urls:
                        contact_urls.append(full)

            for curl in contact_urls[:4]:
                html2 = await self._fetch(session, curl)
                if not html2:
                    continue
                for href in re.findall(r'href=["\']mailto:([^"\'?\s]+)', html2, re.I):
                    if "@" in href:
                        return href.strip()
                email = _parse_email(html2)
                if email != "N/A":
                    return email

        except Exception:
            pass
        return "N/A"

    async def _fetch(self, session: aiohttp.ClientSession, url: str) -> str:
        """Fetch URL and return decoded text. Returns '' on any error."""
        try:
            async with session.get(url, allow_redirects=True, max_redirects=5) as resp:
                if resp.status >= 400:
                    return ""
                raw = await resp.read()
                enc = resp.charset or "utf-8"
                return raw.decode(enc, errors="replace")
        except Exception:
            return ""

    async def _playwright_email(self, context: BrowserContext, website: str) -> str:
        """Playwright-based email extraction — used only when aiohttp finds nothing."""
        tab = None
        try:
            tab = await context.new_page()
            await self._block_resources(tab, block_stylesheets=True)

            try:
                await tab.goto(website, wait_until="domcontentloaded", timeout=12000)
            except Exception:
                try:
                    await tab.goto(website, wait_until="commit", timeout=8000)
                except Exception:
                    return "N/A"

            await tab.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await tab.wait_for_timeout(800)
            email = await self._pw_scan(tab)
            if email != "N/A":
                return email

            try:
                links = await tab.evaluate('''() =>
                    Array.from(document.querySelectorAll('a[href]')).map(a => a.href)
                ''')
            except Exception:
                links = []

            contact_urls = [
                h for h in links
                if h.startswith("http") and any(kw in h.lower() for kw in _CONTACT_KW)
            ]

            for curl in contact_urls[:3]:
                try:
                    await tab.goto(curl, wait_until="domcontentloaded", timeout=8000)
                    await tab.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await tab.wait_for_timeout(600)
                    email = await self._pw_scan(tab)
                    if email != "N/A":
                        return email
                except Exception:
                    continue

        except Exception:
            pass
        finally:
            if tab:
                try:
                    await tab.close()
                except Exception:
                    pass
        return "N/A"

    async def _pw_scan(self, page: Page) -> str:
        try:
            links = await page.evaluate('''() =>
                Array.from(document.querySelectorAll('a[href^="mailto:"]')).map(a => a.href)
            ''')
            for raw in links:
                e = raw.replace("mailto:", "").split("?")[0].strip()
                if e and "@" in e:
                    return e
            return _parse_email(await page.content())
        except Exception:
            return "N/A"

    # ──────────────────────────────────────────────────────────────
    # CSV
    # ──────────────────────────────────────────────────────────────

    _FIELDS = [
        "business_name", "category", "address", "phone_number",
        "email_address", "website", "rating", "total_reviews",
        "google_maps_url", "social_links", "raw_contact_info",
    ]

    def _init_csv(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        # Only write header if file doesn't exist yet (city-by-city appending)
        if not os.path.exists(path):
            with open(path, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=self._FIELDS).writeheader()

    def _append_to_csv(self, path: str, leads: List[BusinessLead]):
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=self._FIELDS)
            for lead in leads:
                w.writerow(lead.model_dump())

    # ──────────────────────────────────────────────────────────────
    # Terminal output
    # ──────────────────────────────────────────────────────────────

    def _print_header(self):
        print(f"{'─'*140}")
        print(
            f" {'#':<5} {'Business':<26} {'Rev':<6} "
            f"{'Phone':<20} {'Email':<28} {'Website':<24} {'Address':<18} Social"
        )
        print(f"{'─'*140}")

    def _print_lead(self, idx: int, lead: BusinessLead):
        name  = lead.business_name[:24]
        rev   = str(lead.total_reviews or 0)
        phone = (lead.phone_number or "N/A")[:19]
        email = (lead.email_address or "N/A")[:27]
        web   = lead.website or "N/A"
        if web != "N/A" and len(web) > 23:
            try:
                web = urlparse(web).netloc[:23]
            except Exception:
                web = web[:23]
        addr  = (lead.address or "N/A")[:17]
        soc   = (
            f"{len(lead.social_links.split(', '))} link(s)"
            if lead.social_links and lead.social_links != "N/A"
            else "N/A"
        )
        print(
            f" {idx:<5} {name:<26} {rev:<6} "
            f"{phone:<20} {email:<28} {web:<24} {addr:<18} {soc}"
        )

    # ──────────────────────────────────────────────────────────────
    # CAPTCHA check
    # ──────────────────────────────────────────────────────────────

    async def _is_captcha(self, page: Page) -> bool:
        try:
            c = await page.content()
            return any(s in c.lower() for s in ["unusual traffic", "captcha", "recaptcha", "are you a robot"])
        except Exception:
            return False
