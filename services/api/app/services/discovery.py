import asyncio
import httpx
from app.schemas import DiscoveryRequest, BusinessCreate
from app.core.config import settings


class DiscoveryError(Exception):
    """Raised when the public OpenStreetMap discovery provider is unavailable."""


GOOGLE_PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
GOOGLE_PLACES_FIELDS = ",".join((
    "places.displayName", "places.formattedAddress", "places.internationalPhoneNumber",
    "places.websiteUri", "places.googleMapsUri", "places.rating", "places.userRatingCount",
    "places.location",
))

CATEGORY_TAGS = {
    "restaurant": [("amenity", "restaurant")],
    "cafe": [("amenity", "cafe")],
    "bar": [("amenity", "bar")],
    "pub": [("amenity", "pub")],
    "salon": [("shop", "hairdresser"), ("shop", "beauty")],
    "gym": [("leisure", "fitness_centre")],
    "hotel": [("tourism", "hotel")],
    "pharmacy": [("amenity", "pharmacy")],
    "dentist": [("amenity", "dentist")],
    "hospital": [("amenity", "hospital")],
}

def _category_filters(category: str) -> str:
    normalized = category.strip().lower()
    if normalized.endswith("s"):
        normalized = normalized[:-1]
    tags = CATEGORY_TAGS.get(normalized, [("amenity", normalized), ("shop", normalized)])
    return "".join(f'nwr["name"]["{key}"="{value}"](area.a);' for key, value in tags)

async def discover_osm(request: DiscoveryRequest) -> list[BusinessCreate]:
    # Overpass is used only for OpenStreetMap data under its published API policy.
    query=f'''[out:json][timeout:25];area["name"="{request.city}"]->.a;({_category_filters(request.category)});out center {request.limit};'''
    data = None
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=35, headers={"User-Agent": "LeadForgeAI/0.2"}) as client:
        # Overpass is a volunteer-run public service; a successful but empty
        # response is occasionally transient, so retry before returning no leads.
        for attempt in range(3):
            try:
                response = await client.post("https://overpass-api.de/api/interpreter", data={"data":query})
                response.raise_for_status()
                candidate = response.json()
                if not isinstance(candidate, dict):
                    raise ValueError("unexpected response format")
                data = candidate
                last_error = None
                if data.get("elements"):
                    break
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(attempt + 1)

    if last_error and data is None:
        raise DiscoveryError(
            f"OpenStreetMap discovery request failed: {last_error}. "
            "Check that the API container can access the internet and try again."
        ) from last_error

    output=[]
    for e in data.get("elements",[]):
        tags=e.get("tags",{}); output.append(BusinessCreate(name=tags.get("name","Unnamed business"), category=request.category, city=request.city, country=request.country, address=" ".join(filter(None,[tags.get("addr:housenumber"),tags.get("addr:street")] )) or None, phone=tags.get("phone") or tags.get("contact:phone"), website=tags.get("website") or tags.get("contact:website"), latitude=e.get("lat") or e.get("center",{}).get("lat"), longitude=e.get("lon") or e.get("center",{}).get("lon")))
    return output


async def discover_google_places(request: DiscoveryRequest) -> list[BusinessCreate]:
    """Discover leads with contact fields from the official Google Places API."""
    if not settings.google_places_api_key:
        raise DiscoveryError(
            "Set GOOGLE_PLACES_API_KEY in .env to discover leads with required "
            "phone number, website, and Google Maps URL."
        )

    payload = {"textQuery": f"{request.category} in {request.city}, {request.country}", "pageSize": min(request.limit, 20)}
    headers = {"X-Goog-Api-Key": settings.google_places_api_key, "X-Goog-FieldMask": GOOGLE_PLACES_FIELDS}
    try:
        async with httpx.AsyncClient(timeout=35) as client:
            response = await client.post(GOOGLE_PLACES_TEXT_SEARCH_URL, headers=headers, json=payload)
            response.raise_for_status()
            places = response.json().get("places", [])
    except (httpx.HTTPError, ValueError) as exc:
        raise DiscoveryError(f"Google Places discovery request failed: {exc}") from exc

    output = []
    for place in places:
        phone = place.get("internationalPhoneNumber")
        website = place.get("websiteUri")
        maps_url = place.get("googleMapsUri")
        # Do not append incomplete leads when these three fields are mandatory.
        if not phone or not website or not maps_url:
            continue
        location = place.get("location", {})
        output.append(BusinessCreate(
            name=place.get("displayName", {}).get("text", "Unnamed business"),
            category=request.category,
            city=request.city,
            country=request.country,
            address=place.get("formattedAddress"),
            phone=phone,
            website=website,
            rating=place.get("rating"),
            review_count=place.get("userRatingCount", 0),
            maps_url=maps_url,
            latitude=location.get("latitude"),
            longitude=location.get("longitude"),
        ))
    return output
