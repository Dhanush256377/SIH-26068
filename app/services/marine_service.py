import requests


def get_marine_weather(
    latitude,
    longitude
):

    try:

        response = requests.get(

            "https://marine-api.open-meteo.com/v1/marine",

            params={

                "latitude":
                    latitude,

                "longitude":
                    longitude,

                "hourly":
                    ",".join([
                        "wave_height",
                        "wave_direction",
                        "wave_period",
                        "wind_wave_height",
                        "wind_wave_direction",
                        "wind_wave_period",
                        "sea_surface_temperature",
                        "ocean_current_velocity",
                        "ocean_current_direction"
                    ]),

                "forecast_days":
                    3,

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
                "Open-Meteo Marine Weather API",

            "location": {
                "latitude":
                    latitude,

                "longitude":
                    longitude
            },

            "timezone":
                data.get(
                    "timezone"
                ),

            "hourly":
                data.get(
                    "hourly",
                    {}
                ),

            "hourly_units":
                data.get(
                    "hourly_units",
                    {}
                ),

            "operational_note":
                "Not suitable for coastal navigation. "
                "Use official nautical information "
                "for operational decisions."
        }

    except requests.RequestException as exc:

        return {

            "success":
                False,

            "message":
                "Unable to retrieve marine "
                "weather data.",

            "error":
                str(exc)
        }