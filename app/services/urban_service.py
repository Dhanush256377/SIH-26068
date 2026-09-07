import requests


def get_urban_weather(latitude, longitude):

    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,

                "current": ",".join([
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "precipitation",
                    "wind_speed_10m",
                    "wind_gusts_10m",
                    "cloud_cover",
                    "weather_code"
                ]),

                "hourly": ",".join([
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "precipitation_probability",
                    "precipitation",
                    "wind_speed_10m",
                    "wind_gusts_10m",
                    "cloud_cover",
                    "weather_code"
                ]),

                "forecast_days": 2,
                "timezone": "auto"
            },

            timeout=20
        )

        response.raise_for_status()

        weather = response.json()

        # Air-quality data
        air_response = requests.get(
            "https://air-quality-api.open-meteo.com/v1/air-quality",
            params={
                "latitude": latitude,
                "longitude": longitude,

                "current": ",".join([
                    "pm10",
                    "pm2_5",
                    "carbon_monoxide",
                    "nitrogen_dioxide",
                    "sulphur_dioxide",
                    "ozone",
                    "us_aqi"
                ]),

                "timezone": "auto"
            },

            timeout=20
        )

        air_quality = {}

        if air_response.ok:
            air_quality = air_response.json()

        return {
            "success": True,

            "source": "Open-Meteo",

            "location": {
                "latitude": latitude,
                "longitude": longitude
            },

            "timezone": weather.get("timezone"),

            "current": weather.get(
                "current",
                {}
            ),

            "hourly": weather.get(
                "hourly",
                {}
            ),

            "air_quality": air_quality.get(
                "current",
                {}
            ),

            "air_quality_units": air_quality.get(
                "current_units",
                {}
            ),

            "note": (
                "Urban weather information "
                "is provided for decision support."
            )
        }

    except requests.RequestException as exc:

        return {
            "success": False,
            "message": (
                "Unable to retrieve urban "
                "weather data."
            ),
            "error": str(exc)
        }