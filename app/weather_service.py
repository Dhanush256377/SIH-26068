import requests
from .config import OPENWEATHER_API_KEY


def get_current_weather(city: str):
    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }

    response = requests.get(url, params=params, timeout=15)

    if response.status_code != 200:
        raise Exception(
            f"OpenWeather error: {response.status_code} "
            f"{response.text}"
        )

    data = response.json()

    return {
        "city": data["name"],
        "country": data["sys"]["country"],
        "temperature": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"],
        "wind_speed": data["wind"]["speed"],
        "weather": data["weather"][0]["description"],
        "latitude": data["coord"]["lat"],
        "longitude": data["coord"]["lon"]
    }