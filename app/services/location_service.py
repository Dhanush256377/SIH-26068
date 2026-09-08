import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org"
OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

HEADERS = {
    "User-Agent": "WeatherGPT-India/2.0 (weather location service)"
}


def search_location(city):
    try:
        response = requests.get(
            OPEN_METEO_GEOCODING_URL,
            params={
                "name": city.strip(),
                "count": 10,
                "language": "en",
                "format": "json",
                "countryCode": "IN",
            },
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return {"error": "Unable to search location"}

    results = data.get("results") or []
    if not results:
        return {"error": "Location not found"}

    locations = []
    for place in results:
        locations.append({
            "name": place.get("name"),
            "latitude": place.get("latitude"),
            "longitude": place.get("longitude"),
            "state": place.get("admin1"),
            "district": place.get("admin2"),
            "country": place.get("country"),
            "timezone": place.get("timezone"),
        })

    return {"results": locations}


def _pick_locality(address):
    """Choose a human locality without allowing a broad district to win."""
    # For map clicks, prefer the actual populated-place hierarchy.
    # Administrative divisions such as county/state_district are only fallbacks.
    return (
        address.get("village")
        or address.get("town")
        or address.get("city")
        or address.get("municipality")
        or address.get("suburb")
        or address.get("neighbourhood")
        or address.get("hamlet")
        or address.get("locality")
        or address.get("quarter")
        or address.get("city_district")
        or address.get("county")
        or address.get("state")
        or "Current Location"
    )


def get_location(latitude, longitude):
    try:
        response = requests.get(
            f"{NOMINATIM_URL}/reverse",
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "jsonv2",
                "zoom": 18,
                "addressdetails": 1,
                "namedetails": 1,
            },
            headers={
                **HEADERS,
                "Accept-Language": "en",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return {
            "error": "Unable to find location",
            "latitude": latitude,
            "longitude": longitude,
            "city": "Current Location",
        }

    address = data.get("address") or {}

    city = _pick_locality(address)
    state = address.get("state") or address.get("state_district") or ""
    district = (
        address.get("county")
        or address.get("state_district")
        or address.get("city_district")
        or ""
    )

    # Keep the more granular fields available to the frontend.
    return {
        "city": city,
        "village": address.get("village", ""),
        "town": address.get("town", ""),
        "municipality": address.get("municipality", ""),
        "suburb": address.get("suburb", ""),
        "neighbourhood": address.get("neighbourhood", ""),
        "hamlet": address.get("hamlet", ""),
        "locality": address.get("locality", ""),
        "road": address.get("road", ""),
        "postcode": address.get("postcode", ""),
        "district": district,
        "state": state,
        "country": address.get("country") or "India",
        "latitude": latitude,
        "longitude": longitude,
        "display_name": data.get("display_name", ""),
        "osm_type": data.get("type", ""),
        "osm_name": data.get("name", ""),
    }
