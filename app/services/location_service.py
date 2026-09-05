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
        "format": "json"
    }

    headers = {
        "User-Agent": "WeatherGPT India"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers
    )

    if response.status_code != 200:
        return {
            "error": "Unable to find location"
        }

    data = response.json()

    address = data.get("address", {})

    return {
        "city": address.get("city")
        or address.get("town")
        or address.get("village"),

        "district": address.get("county"),

        "state": address.get("state"),

        "country": address.get("country")
    }