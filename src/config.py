"""
Configuration — loaded from environment / .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Nominatim (no API key needed)
    nominatim_user_agent: str = Field(
        default="maps-lead-gen-scraper/1.0",
        description="User-Agent for Nominatim API",
    )

    # Browser
    headless: bool = Field(default=True)

    # Phase 1 — scroll settings
    max_scroll_attempts: int = Field(
        default=15,
        description="Consecutive empty scrolls before stopping",
    )
    max_total_scrolls: int = Field(
        default=500,
        description="Hard cap on total scroll iterations",
    )
    scroll_delay_min: float = Field(default=1.0)
    scroll_delay_max: float = Field(default=2.2)

    # Phase 2 — parallel workers
    detail_workers: int = Field(
        default=8,
        description="Concurrent Maps detail pages (each also opens an aiohttp session)",
    )
    web_workers: int = Field(
        default=20,
        description="Max concurrent aiohttp HTTP requests for email hunting",
    )
    playwright_fallback_workers: int = Field(
        default=3,
        description="Concurrent Playwright tabs used only when aiohttp fails (JS-heavy sites)",
    )


settings = Settings()
