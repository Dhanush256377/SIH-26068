from fastapi import APIRouter
from app.services.weather_service import get_weather, get_historical_weather, get_forecast, get_climate_analysis
router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("/")
def weather(latitude: float, longitude: float):
    return get_weather(latitude, longitude)


@router.get("/historical")
def historical_weather(latitude: float, longitude: float):
    return get_historical_weather(latitude, longitude)
@router.get("/forecast")
def forecast(latitude: float, longitude: float):
    return get_forecast(latitude, longitude)
