"""
Data models for scraped business leads.
"""

from pydantic import BaseModel, Field
from typing import Optional


class BusinessLead(BaseModel):
    """Schema for a single business extracted from Google Maps."""

    business_name: str = Field(..., description="Name of the business")
    category: str = Field(default="N/A", description="Business category")
    address: str = Field(default="N/A", description="Full address")
    phone_number: Optional[str] = Field(default="N/A", description="Phone number")
    email_address: Optional[str] = Field(default="N/A", description="Email Address")
    website: Optional[str] = Field(default="N/A", description="Website URL")
    rating: Optional[float] = Field(default=0.0, description="Google rating (0-5)")
    total_reviews: Optional[int] = Field(default=0, description="Total review count")
    google_maps_url: Optional[str] = Field(default="N/A", description="Google Maps link")
    social_links: Optional[str] = Field(default="N/A", description="Social media links (comma-separated)")
    raw_contact_info: Optional[str] = Field(default="N/A", description="Raw text containing phones/emails found on the site")


class LocationResult(BaseModel):
    """Schema for a location returned by Nominatim."""

    display_name: str
    lat: float
    lon: float
    place_type: str = Field(default="unknown")
