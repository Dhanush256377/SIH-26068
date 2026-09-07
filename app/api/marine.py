from fastapi import APIRouter, Query

from app.services.marine_service import (
    get_marine_weather
)


router = APIRouter(
    prefix="/marine",
    tags=["Marine"]
)


@router.get("/weather")
def marine_weather(

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

    return get_marine_weather(
        latitude,
        longitude
    )