from fastapi import APIRouter, Query

from app.services.weather_service import get_weather
from app.services.agriculture_service import (
    get_agriculture_advice
)


router = APIRouter(
    prefix="/agriculture",
    tags=["Agriculture"]
)


@router.get("/")
def agriculture(
    crop: str = Query(
        ...,
        min_length=1
    ),

    latitude: float = Query(
        ...,
        ge=-90,
        le=90
    ),

    longitude: float = Query(
        ...,
        ge=-180,
        le=180
    ),

    growth_stage: str | None = Query(
        None
    )
):

    weather = get_weather(
        latitude,
        longitude
    )

    if "error" in weather:
        return weather

    advice = get_agriculture_advice(
        crop=crop,
        weather=weather,
        growth_stage=growth_stage
    )

    return {
        "success": True,
        "weather": weather,
        "agriculture_advice": advice
    }