from fastapi import APIRouter
from app.services.weather_service import get_weather
from app.services.alert_service import generate_alerts

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/")
def alerts(latitude: float, longitude: float):

    weather = get_weather(latitude, longitude)

    if "error" in weather:
        return weather

    alerts = generate_alerts(weather)

    return {
        "alerts": alerts,
        "weather": weather
    }