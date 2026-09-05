from fastapi import APIRouter
from app.services.weather_service import get_weather
from app.services.agriculture_service import get_agriculture_advice

router = APIRouter(prefix="/agriculture", tags=["Agriculture"])


@router.get("/")
def agriculture(crop: str, latitude: float, longitude: float):

    weather = get_weather(latitude, longitude)

    if "error" in weather:
        return weather

    advice = get_agriculture_advice(crop, weather)

    return {
        "weather": weather,
        "agriculture_advice": advice
    }