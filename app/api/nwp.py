from fastapi import APIRouter, Query

from app.services.nwp_service import (
    get_nwp_forecast
)


router = APIRouter(
    prefix="/nwp",
    tags=["NWP"]
)


@router.get("/forecast")
def nwp_forecast(

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

    model: str = Query(
        "gfs"
    ),

    forecast_days: int = Query(
        3,
        ge=1,
        le=16
    )
):

    return get_nwp_forecast(
        latitude=latitude,
        longitude=longitude,
        model=model,
        forecast_days=forecast_days
    )