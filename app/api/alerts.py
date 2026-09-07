from fastapi import APIRouter
from app.services.weather_service import get_weather
from app.services.alert_service import generate_alerts

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/")
def alerts(latitude: float, longitude: float):

    weather = get_weather(
        latitude,
        longitude
    )

    if weather.get("error"):
        return {
            "error": weather["error"],
            "alerts": []
        }

    alert_weather = {
        "temperature": weather.get("temperature"),
        "wind_speed": weather.get("wind_speed"),
        "rain": weather.get("rain"),
        "precipitation": weather.get("precipitation"),
        "humidity": weather.get("humidity"),
        "weather_code": weather.get("weather_code")
    }

    return {
        "latitude": latitude,
        "longitude": longitude,
        "alerts": generate_alerts(alert_weather)
    }