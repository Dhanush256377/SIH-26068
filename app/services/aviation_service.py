import requests


def get_aviation_weather(
    latitude,
    longitude
):

    try:

        response = requests.get(

            "https://api.open-meteo.com/v1/forecast",

            params={

                "latitude":
                    latitude,

                "longitude":
                    longitude,

                "current":
                    ",".join([
                        "temperature_2m",
                        "relative_humidity_2m",
                        "pressure_msl",
                        "visibility",
                        "wind_speed_10m",
                        "wind_direction_10m",
                        "wind_gusts_10m",
                        "cloud_cover",
                        "weather_code"
                    ]),

                "hourly":
                    ",".join([
                        "visibility",
                        "wind_speed_10m",
                        "wind_direction_10m",
                        "wind_gusts_10m",
                        "cloud_cover",
                        "cloud_base",
                        "weather_code",
                        "precipitation_probability",
                        "temperature_2m"
                    ]),

                "forecast_hours":
                    24,

                "timezone":
                    "auto"
            },

            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        return {

            "success":
                True,

            "source":
                "Open-Meteo forecast data",

            "location": {
                "latitude":
                    latitude,

                "longitude":
                    longitude
            },

            "timezone":
                data.get("timezone"),

            "current":
                data.get(
                    "current",
                    {}
                ),

            "hourly":
                data.get(
                    "hourly",
                    {}
                ),

            "operational_note":
                "Decision support only. "
                "Not flight clearance or a "
                "METAR/TAF replacement."
        }

    except requests.RequestException as exc:

        return {

            "success":
                False,

            "message":
                "Unable to retrieve aviation "
                "weather data.",

            "error":
                str(exc)
        }