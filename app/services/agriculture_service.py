def _first(value, default=0):

    if (
        isinstance(value, list)
        and value
    ):
        return value[0]

    return default


def get_agriculture_advice(
    crop,
    weather,
    growth_stage=None
):

    crop = (
        crop or "crop"
    ).strip()

    stage = (
        growth_stage
        or "not specified"
    ).strip()

    temperature = weather.get(
        "temperature"
    )

    humidity = weather.get(
        "humidity"
    )

    wind_speed = (
        weather.get("wind_speed")
        or 0
    )

    wind_gust = (
        weather.get("wind_gust")
        or 0
    )

    daily = (
        weather.get("daily")
        or {}
    )

    rain_probability = _first(
        daily.get(
            "precipitation_probability_max"
        )
    )

    rainfall = _first(
        daily.get(
            "precipitation_sum"
        )
    )

    advice = []
    risks = []

    # -----------------------------------------------------
    # Rain
    # -----------------------------------------------------

    if rain_probability >= 70:

        advice.append(
            f"High rain probability "
            f"({rain_probability}%). "
            "Avoid unnecessary irrigation "
            "and spraying immediately before rainfall."
        )

        risks.append(
            "heavy_rain_risk"
        )

    elif rain_probability >= 40:

        advice.append(
            f"Moderate rain probability "
            f"({rain_probability}%). "
            "Check soil moisture before irrigation."
        )

    else:

        advice.append(
            f"Low rain probability "
            f"({rain_probability}%). "
            "Irrigation may be needed depending "
            "on soil moisture and crop stage."
        )

    # -----------------------------------------------------
    # Rainfall
    # -----------------------------------------------------

    if rainfall >= 20:

        advice.append(
            f"Forecast rainfall is about "
            f"{rainfall} mm. "
            "Check drainage and low-lying areas."
        )

        risks.append(
            "waterlogging_risk"
        )

    # -----------------------------------------------------
    # Heat
    # -----------------------------------------------------

    if (
        temperature is not None
        and temperature >= 38
    ):

        advice.append(
            f"High temperature "
            f"({temperature} °C). "
            "Prioritize water availability "
            "and monitor heat stress."
        )

        risks.append(
            "heat_stress"
        )

    elif (
        temperature is not None
        and temperature <= 15
    ):

        advice.append(
            f"Low temperature "
            f"({temperature} °C). "
            "Monitor temperature-sensitive crops."
        )

        risks.append(
            "cold_stress"
        )

    # -----------------------------------------------------
    # Humidity
    # -----------------------------------------------------

    if (
        humidity is not None
        and humidity >= 80
    ):

        advice.append(
            f"High humidity "
            f"({humidity}%). "
            "Monitor dense canopy areas "
            "for fungal disease pressure."
        )

        risks.append(
            "fungal_pressure"
        )

    # -----------------------------------------------------
    # Wind
    # -----------------------------------------------------

    if (
        wind_gust >= 40
        or wind_speed >= 30
    ):

        advice.append(
            f"Strong wind conditions "
            f"({wind_speed} km/h, "
            f"gusts {wind_gust} km/h). "
            "Delay spraying where practical."
        )

        risks.append(
            "wind_risk"
        )

    # -----------------------------------------------------
    # Crop-specific advice
    # -----------------------------------------------------

    crop_notes = {

        "rice":
            "For rice, pay attention to standing water, "
            "drainage and high humidity.",

        "paddy":
            "For paddy, pay attention to standing water, "
            "drainage and high humidity.",

        "cotton":
            "For cotton, monitor flowering and boll "
            "stages during heat, rain and high humidity.",

        "maize":
            "For maize, monitor soil moisture and "
            "lodging risk during strong winds or heavy rain.",

        "wheat":
            "For wheat, avoid unnecessary irrigation "
            "before substantial rainfall.",

        "onion":
            "For onion, avoid prolonged leaf wetness "
            "and waterlogging."
    }

    crop_note = crop_notes.get(
        crop.lower()
    )

    if crop_note:
        advice.append(
            crop_note
        )

    # -----------------------------------------------------
    # Final recommendation
    # -----------------------------------------------------

    advice.append(
        f"Continue regular pest and disease "
        f"scouting for {crop}. "
        f"Growth stage: {stage}."
    )

    return {

        "crop": crop,

        "growth_stage":
            stage,

        "advice":
            advice,

        "risk_flags":
            sorted(set(risks)),

        "weather_summary": {

            "temperature_c":
                temperature,

            "humidity_pct":
                humidity,

            "rain_probability_pct":
                rain_probability,

            "rainfall_mm":
                rainfall,

            "wind_kmh":
                wind_speed,

            "gust_kmh":
                wind_gust
        },

        "disclaimer":
            "Weather-based guidance is decision support, "
            "not crop-disease diagnosis."
    }