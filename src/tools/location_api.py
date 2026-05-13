"""
Location Discovery Tool — uses Nominatim (OpenStreetMap) for free geocoding.
No API key required.
"""

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from src.config import settings
from src.models import LocationResult
from typing import List


class LocationDiscoveryTool:
    """
    Discovers sub-regions/localities within a broad area using Nominatim.
    Free, no API key needed. Rate-limited to 1 req/sec per Nominatim TOS.
    """

    def __init__(self):
        self.geolocator = Nominatim(user_agent=settings.nominatim_user_agent)
        # Rate limiter: 1 request per second (Nominatim policy)
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1.0)

    def discover_locations(self, area: str) -> List[LocationResult]:
        """
        Given a broad area (e.g. 'Luxembourg'), return a list of
        sub-regions, cities, and notable localities.
        """
        results: List[LocationResult] = []

        # Search for the area and its sub-regions
        raw_results = self.geolocator.geocode(
            area,
            exactly_one=False,
            limit=15,
            addressdetails=True,
            language="en",
        )

        if not raw_results:
            return results

        for loc in raw_results:
            try:
                addr = loc.raw.get("address", {})
                place_type = loc.raw.get("type", "unknown")

                results.append(
                    LocationResult(
                        display_name=loc.address,
                        lat=float(loc.latitude),
                        lon=float(loc.longitude),
                        place_type=place_type,
                    )
                )
            except (ValueError, KeyError):
                continue

        # Also try to find sub-cities/towns within the main area
        sub_queries = [
            f"cities in {area}",
            f"towns in {area}",
            f"{area} districts",
        ]

        for query in sub_queries:
            try:
                sub_results = self.geolocator.geocode(
                    query,
                    exactly_one=False,
                    limit=10,
                    language="en",
                )
                if sub_results:
                    for loc in sub_results:
                        display = loc.address
                        # Avoid duplicates
                        if not any(r.display_name == display for r in results):
                            results.append(
                                LocationResult(
                                    display_name=display,
                                    lat=float(loc.latitude),
                                    lon=float(loc.longitude),
                                    place_type=loc.raw.get("type", "unknown"),
                                )
                            )
            except Exception:
                continue

        return results
