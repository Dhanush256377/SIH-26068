import requests


NWP_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation_probability",
    "precipitation",
    "rain",
    "weather_code",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "surface_pressure",
    "cloud_cover",
    "visibility",
    "cape"
]


def get_nwp_forecast(
    latitude,
    longitude,
    model="gfs",
    forecast_days=3
):

    selected_model = (
        model or "gfs"
    ).lower()

    # -----------------------------------------------------
    # Only GFS is actually configured
    # -----------------------------------------------------

    if selected_model not in (
        "gfs",
        "gfs_seamless",
        "gfs_global"
    ):

        return {
            "success": False,
            "model": selected_model.upper(),

            "message":
                "Only GFS is configured. "
                "WRF is not enabled because "
                "no WRF data source is configured."
        }

    try:

        days = max(
            1,
            min(
                int(forecast_days),
                16
            )
        )

    except (
        TypeError,
        ValueError
    ):

        days = 3

    try:

        response = requests.get(

            "https://api.open-meteo.com/v1/forecast",

            params={

                "latitude":
                    latitude,

                "longitude":
                    longitude,

                "hourly":
                    ",".join(
                        NWP_VARIABLES
                    ),

                "forecast_days":
                    days,

                "models":
                    "gfs_seamless",

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

            "model":
                "GFS",

            "provider":
                "NOAA GFS via Open-Meteo",

            "latitude":
                data.get(
                    "latitude",
                    latitude
                ),

            "longitude":
                data.get(
                    "longitude",
                    longitude
                ),

            "timezone":
                data.get(
                    "timezone"
                ),

            "elevation":
                data.get(
                    "elevation"
                ),

            "forecast_days":
                days,

            "hourly":
                data.get(
                    "hourly",
                    {}
                ),

            "hourly_units":
                data.get(
                    "hourly_units",
                    {}
                )
        }

    except requests.RequestException as exc:

        return {

            "success":
                False,

            "model":
                "GFS",

            "message":
                "Unable to retrieve GFS "
                "forecast data.",

            "error":
                str(exc)
        }