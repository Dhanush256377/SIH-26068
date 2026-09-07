from fastapi import APIRouter, Query

from app.services.urban_service import (
    get_urban_weather
)


router = APIRouter(
    prefix="/urban",
    tags=["Urban Weather"]
)


@router.get("/weather")
def urban_weather(

    latitude: float = Query(
        ...,
        ge=-90,
        le=90
    ),

    longitude: float = Query(
        ...,
        ge=-180,
        le=180
    )
):

    return get_urban_weather(
        latitude,
        longitude
    )