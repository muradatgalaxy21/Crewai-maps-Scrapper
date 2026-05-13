"""
Orchestration pipeline.

For broad areas (states, countries) Google Maps caps results to ~20.
This pipeline detects that and automatically scrapes city-by-city,
deduplicating by business name across all cities.
"""

import asyncio
import re
from typing import List

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from src.tools.playwright_bot import StealthScraperTool
from src.models import BusinessLead
from src.config import settings

# Nominatim place types that indicate a broad area (state / country level)
_BROAD_TYPES = {
    "administrative", "country", "state", "region",
    "province", "territory", "county",
}

# Major cities to query when the selected location is a broad area.
# Add more as needed.
_STATE_CITIES = {
    "florida": [
        "Miami", "Orlando", "Tampa", "Jacksonville", "Fort Lauderdale",
        "St. Petersburg", "Tallahassee", "Cape Coral", "Hialeah", "Gainesville",
        "Pembroke Pines", "Hollywood", "Miramar", "Coral Springs", "Clearwater",
        "Port St. Lucie", "Lakeland", "Palm Bay", "Pompano Beach", "West Palm Beach",
        "Boca Raton", "Davie", "Sunrise", "Deltona", "Fort Myers",
        "Daytona Beach", "Sarasota", "Naples", "Kissimmee", "Ocala",
    ],
    "texas": [
        "Houston", "San Antonio", "Dallas", "Austin", "Fort Worth",
        "El Paso", "Arlington", "Corpus Christi", "Plano", "Lubbock",
        "Laredo", "Irving", "Garland", "Frisco", "McKinney",
        "Amarillo", "Grand Prairie", "Brownsville", "Killeen", "McAllen",
    ],
    "california": [
        "Los Angeles", "San Diego", "San Jose", "San Francisco", "Fresno",
        "Sacramento", "Long Beach", "Oakland", "Bakersfield", "Anaheim",
        "Santa Ana", "Riverside", "Stockton", "Irvine", "Chula Vista",
        "Fremont", "San Bernardino", "Modesto", "Fontana", "Moreno Valley",
    ],
    "new york": [
        "New York City", "Buffalo", "Rochester", "Yonkers", "Syracuse",
        "Albany", "New Rochelle", "Mount Vernon", "Schenectady", "Utica",
    ],
    "illinois": [
        "Chicago", "Aurora", "Naperville", "Joliet", "Rockford",
        "Springfield", "Elgin", "Peoria", "Champaign", "Waukegan",
    ],
    "pennsylvania": [
        "Philadelphia", "Pittsburgh", "Allentown", "Erie", "Reading",
        "Scranton", "Bethlehem", "Lancaster", "Harrisburg", "York",
    ],
    "ohio": [
        "Columbus", "Cleveland", "Cincinnati", "Toledo", "Akron",
        "Dayton", "Parma", "Canton", "Lorain", "Hamilton",
    ],
    "georgia": [
        "Atlanta", "Augusta", "Columbus", "Savannah", "Athens",
        "Sandy Springs", "Roswell", "Macon", "Johns Creek", "Albany",
    ],
    "north carolina": [
        "Charlotte", "Raleigh", "Greensboro", "Durham", "Winston-Salem",
        "Fayetteville", "Cary", "Wilmington", "High Point", "Concord",
    ],
    "michigan": [
        "Detroit", "Grand Rapids", "Warren", "Sterling Heights", "Ann Arbor",
        "Lansing", "Flint", "Dearborn", "Livonia", "Westland",
    ],
}


def _normalize(s: str) -> str:
    return re.sub(r'[^a-z]', '', s.lower())


def _get_cities_for_location(display_name: str, place_type: str) -> List[str]:
    """
    Return a list of cities to scrape if the location is broad,
    or an empty list if it is already a city-level location.
    """
    if place_type not in _BROAD_TYPES:
        return []

    dn_lower = display_name.lower()
    for key, cities in _STATE_CITIES.items():
        if key in dn_lower:
            return cities
    return []


class ScrapingPipeline:
    def __init__(self):
        self.scraper = StealthScraperTool()
        geolocator = Nominatim(user_agent=settings.nominatim_user_agent)
        self._geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.0)

    def run(
        self,
        location: str,
        business_type: str,
        output_file: str = "leads_output.csv",
        place_type: str = "unknown",
    ) -> List[BusinessLead]:
        return asyncio.run(
            self._run_async(location, business_type, output_file, place_type)
        )

    async def _run_async(
        self,
        location: str,
        business_type: str,
        output_file: str,
        place_type: str,
    ) -> List[BusinessLead]:

        cities = _get_cities_for_location(location, place_type)

        if not cities:
            # Single location — scrape directly
            return await self.scraper.scrape(
                location=location,
                business_type=business_type,
                output_file=output_file,
            )

        # City-by-city scraping
        print(
            f"\n  BROAD AREA DETECTED — will scrape {len(cities)} cities one by one.\n"
        )

        all_results: List[BusinessLead] = []
        seen_names: set = set()

        for idx, city in enumerate(cities, 1):
            city_location = f"{city}, {location}"
            print(f"\n  ── [{idx}/{len(cities)}] {city_location} ──")

            # Fresh scraper per city so internal state is clean
            city_scraper = StealthScraperTool()
            results = await city_scraper.scrape(
                location=city_location,
                business_type=business_type,
                output_file=output_file,   # all cities append to same CSV
            )

            added = 0
            for lead in results:
                key = _normalize(lead.business_name)
                if key not in seen_names:
                    seen_names.add(key)
                    all_results.append(lead)
                    added += 1

            print(f"  {added} new unique leads from {city} (total so far: {len(all_results)})")

        return all_results
