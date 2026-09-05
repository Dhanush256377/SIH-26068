def get_agriculture_advice(crop, weather):

    temperature = weather.get(
        "temperature",
        0
    )


    humidity = weather.get(
        "humidity",
        0
    )


    daily = weather.get(
        "daily",
        {}
    )


    rain_probability = 0


    if daily.get(
        "precipitation_probability_max"
    ):

        rain_probability = (
            daily[
                "precipitation_probability_max"
            ][0] or 0
        )


    advice = []


    if rain_probability >= 70:

        advice.append(
            f"High chance of rain ({rain_probability}%). "
            "Avoid unnecessary irrigation."
        )

        advice.append(
            "Avoid spraying pesticides immediately before rainfall."
        )


    elif rain_probability >= 40:

        advice.append(
            f"Moderate rain probability ({rain_probability}%). "
            "Monitor the field before irrigation."
        )


    else:

        advice.append(
            f"Low rain probability ({rain_probability}%). "
            "Irrigation may be required depending on soil moisture."
        )


    if temperature >= 35:

        advice.append(
            f"High temperature ({temperature} °C). "
            "Provide sufficient water and monitor crops for heat stress."
        )


    elif temperature <= 20:

        advice.append(
            f"Temperature is relatively low ({temperature} °C). "
            "Monitor temperature-sensitive crops."
        )


    else:

        advice.append(
            f"Temperature ({temperature} °C) is suitable "
            "for normal crop monitoring."
        )


    if humidity >= 80:

        advice.append(
            f"High humidity ({humidity}%). "
            "Monitor crops for fungal diseases."
        )


    advice.append(
        f"Continue regular monitoring of {crop} "
        "for pests and diseases."
    )


    return {

        "crop": crop,

        "advice": advice

    }