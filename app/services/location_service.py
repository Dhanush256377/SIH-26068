import requests

def search_location(city):

    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": city,
        "count": 10,
        "language": "en",
        "format": "json",
        "countryCode": "IN"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return {"error": "Unable to search location"}

    data = response.json()

    if "results" not in data:
        return {"error": "Location not found"}

    locations = []

    for place in data["results"]:

        locations.append({
            "name": place.get("name"),
            "latitude": place.get("latitude"),
            "longitude": place.get("longitude"),
            "state": place.get("admin1"),
            "district": place.get("admin2"),
            "country": place.get("country")
        })

    return {
        "results": locations
    }

def get_location(latitude, longitude):

    url = "https://nominatim.openstreetmap.org/reverse"

    params = {
        "lat": latitude,
        "lon": longitude,
        "format": "json",
        "zoom": 10,
        "addressdetails": 1
    }

    headers = {
        "User-Agent": "WeatherGPT India/1.0"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10
    )

    if response.status_code != 200:
        return {
            "error": "Unable to find location"
        }

    data = response.json()
    address = data.get("address", {})

    city = (
        address.get("city")
        or address.get("town")
        or address.get("municipality")
        or address.get("city_district")
        or address.get("village")
        or address.get("suburb")
        or address.get("county")
        or "Current Location"
    )

    district = (
        address.get("county")
        or address.get("state_district")
        or address.get("city_district")
        or ""
    )

    state = address.get("state") or ""

    country = address.get("country") or "India"

    return {
        "city": city,
        "district": district,
        "state": state,
        "country": country
    }