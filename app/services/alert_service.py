def generate_alerts(weather):

    alerts = []

    temperature = weather["temperature"]
    wind_speed = weather["wind_speed"]
    rain_probability = weather["rain_probability"]

    if rain_probability >= 70:
        alerts.append({
            "type": "Heavy Rain",
            "severity": "High",
            "message": "High chance of rain. Carry an umbrella and plan travel carefully."
        })

    elif rain_probability >= 40:
        alerts.append({
            "type": "Rain",
            "severity": "Medium",
            "message": "There is a chance of rain today."
        })

    if temperature >= 40:
        alerts.append({
            "type": "Heat",
            "severity": "High",
            "message": "Very high temperature detected. Avoid prolonged exposure to heat."
        })

    elif temperature >= 35:
        alerts.append({
            "type": "High Temperature",
            "severity": "Medium",
            "message": "Temperature is high today. Stay hydrated."
        })

    if wind_speed >= 50:
        alerts.append({
            "type": "Strong Wind",
            "severity": "High",
            "message": "Strong winds are expected. Take necessary precautions."
        })

    if not alerts:
        alerts.append({
            "type": "Normal",
            "severity": "Low",
            "message": "No major weather alerts at this time."
        })

    return alerts