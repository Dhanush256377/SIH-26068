from fastapi import APIRouter, Query

from app.services.aviation_service import (
    get_aviation_weather
)


router = APIRouter(
    prefix="/aviation",
    tags=["Aviation"]
)


@router.get("/weather")
def aviation_weather(

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

    return get_aviation_weather(
        latitude,
        longitude
    )