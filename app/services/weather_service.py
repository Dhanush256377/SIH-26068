import requests


def get_weather(latitude, longitude):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

       "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m",

        "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,precipitation,rain,weather_code,cloud_cover,wind_speed_10m,wind_gusts_10m",

        "daily": "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,precipitation_sum,rain_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,sunrise,sunset",

        "forecast_days": 7,

        "timezone": "auto"
    }

    response = requests.get(url, params=params, timeout=15)

    if response.status_code != 200:
        return {
            "error": "Unable to get live weather data"
        }

    data = response.json()

    return {
    "temperature": data["current"]["temperature_2m"],
    "humidity": data["current"]["relative_humidity_2m"],
    "feels_like": data["current"]["apparent_temperature"],
    "precipitation": data["current"]["precipitation"],
    "rain": data["current"]["rain"],
    "weather_code": data["current"]["weather_code"],
    "cloud_cover": data["current"]["cloud_cover"],
    "wind_speed": data["current"]["wind_speed_10m"],
    "wind_direction": data["current"]["wind_direction_10m"],
    "wind_gust": data["current"]["wind_gusts_10m"],
    "hourly": data["hourly"],
    "daily": data["daily"]
}


def get_forecast(latitude, longitude):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "hourly": "temperature_2m,apparent_temperature,precipitation_probability,precipitation,rain,weather_code,relative_humidity_2m,wind_speed_10m,wind_gusts_10m,cloud_cover",

        "daily": "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,sunrise,sunset",

        "forecast_days": 7,

        "timezone": "auto"
    }

    response = requests.get(url, params=params, timeout=15)

    if response.status_code != 200:
        return {
            "error": "Unable to get forecast"
        }

    data = response.json()

    return {
        "hourly": data["hourly"],
        "daily": data["daily"]
    }


def get_historical_weather(latitude, longitude):

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "start_date": "2025-01-01",
        "end_date": "2025-01-07",

        "daily": "temperature_2m_mean,precipitation_sum",

        "timezone": "auto"
    }

    response = requests.get(url, params=params, timeout=15)

    if response.status_code != 200:
        return {
            "error": "Unable to get historical weather"
        }

    data = response.json()

    return {
        "dates": data["daily"]["time"],
        "temperature": data["daily"]["temperature_2m_mean"],
        "rainfall": data["daily"]["precipitation_sum"]
    }


def get_climate_analysis(latitude, longitude):

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "start_date": "2025-01-01",
        "end_date": "2025-12-31",

        "daily": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum",

        "timezone": "auto"
    }

    response = requests.get(url, params=params, timeout=15)

    if response.status_code != 200:
        return {
            "error": "Unable to get climate data"
        }

    data = response.json()

    temperatures = [
        x for x in data["daily"]["temperature_2m_mean"]
        if x is not None
    ]

    rainfall = [
        x for x in data["daily"]["precipitation_sum"]
        if x is not None
    ]

    maximum_temperatures = [
        x for x in data["daily"]["temperature_2m_max"]
        if x is not None
    ]

    minimum_temperatures = [
        x for x in data["daily"]["temperature_2m_min"]
        if x is not None
    ]

    average_temperature = (
        sum(temperatures) / len(temperatures)
        if temperatures else 0
    )

    total_rainfall = sum(rainfall)

    return {
        "year": 2025,
        "average_temperature": round(average_temperature, 2),
        "total_rainfall": round(total_rainfall, 2),
        "maximum_temperature": max(maximum_temperatures)
        if maximum_temperatures else 0,
        "minimum_temperature": min(minimum_temperatures)
        if minimum_temperatures else 0
    }