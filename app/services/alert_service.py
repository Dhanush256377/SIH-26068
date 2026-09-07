def generate_alerts(weather):

    alerts = []

    temperature = weather.get("temperature")
    wind_speed = weather.get("wind_speed")
    rain = weather.get("rain")
    precipitation = weather.get("precipitation")
    humidity = weather.get("humidity")
    weather_code = weather.get("weather_code")

    if temperature is not None:

        if temperature >= 40:
            alerts.append({
                "type": "Extreme Heat",
                "severity": "High",
                "source": "WeatherGPT",
                "message": "Extreme heat detected. Avoid prolonged outdoor exposure and stay hydrated."
            })

        elif temperature >= 35:
            alerts.append({
                "type": "High Temperature",
                "severity": "Medium",
                "source": "WeatherGPT",
                "message": "High temperature detected. Stay hydrated and avoid prolonged outdoor activity."
            })

    if rain is not None or precipitation is not None:

        rain_value = rain if rain is not None else precipitation

        if rain_value >= 20:
            alerts.append({
                "type": "Heavy Rain",
                "severity": "High",
                "source": "WeatherGPT",
                "message": "Heavy rainfall is occurring or expected. Take care while travelling and watch for waterlogging."
            })

        elif rain_value > 0:
            alerts.append({
                "type": "Rain",
                "severity": "Medium",
                "source": "WeatherGPT",
                "message": "Rain is currently occurring. Consider carrying an umbrella."
            })

    if wind_speed is not None:

        if wind_speed >= 60:
            alerts.append({
                "type": "Extreme Wind",
                "severity": "High",
                "source": "WeatherGPT",
                "message": "Very strong winds detected. Avoid exposed and unsafe outdoor areas."
            })

        elif wind_speed >= 40:
            alerts.append({
                "type": "Strong Wind",
                "severity": "Medium",
                "source": "WeatherGPT",
                "message": "Strong winds detected. Use extra caution outdoors."
            })

    if humidity is not None and humidity >= 90:
        alerts.append({
            "type": "High Humidity",
            "severity": "Low",
            "source": "WeatherGPT",
            "message": "Very high humidity detected. Stay hydrated and take breaks during outdoor activity."
        })

    if weather_code in [95, 96, 99]:
        alerts.append({
            "type": "Thunderstorm",
            "severity": "High",
            "source": "WeatherGPT",
            "message": "Thunderstorm conditions detected. Avoid exposed outdoor areas and monitor official warnings."
        })

    if not alerts:
        alerts.append({
            "type": "Normal",
            "severity": "Low",
            "source": "WeatherGPT",
            "message": "No major weather-based alerts at this time."
        })

    return alerts