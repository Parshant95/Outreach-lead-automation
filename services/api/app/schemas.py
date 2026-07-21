from pydantic import BaseModel, Field

class BusinessCreate(BaseModel):
    name: str
    category: str | None = None
    city: str | None = None
    country: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    rating: float | None = None
    review_count: int = 0
    maps_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None

class DiscoveryRequest(BaseModel):
    country: str
    state: str | None = None
    city: str
    category: str
    limit: int = Field(20, ge=1, le=100)

class OutreachRequest(BaseModel):
    channel: str = Field(pattern="^(whatsapp|email|instagram|linkedin)$")
