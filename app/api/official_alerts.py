from fastapi import APIRouter, Query, HTTPException

from app.services.official_alert_service import (
    get_official_alerts,
    get_active_official_alerts,
)

router = APIRouter(
    prefix="/official-alerts",
    tags=["Official Alerts"]
)


@router.get("/")
def official_alerts(
    identifier: str = Query(..., min_length=1)
):
    """
    Get one official SACHET alert using its identifier.
    """
    return get_official_alerts(identifier)


@router.get("/active")
def active_official_alerts(
    latitude: float | None = Query(
        None,
        ge=-90,
        le=90
    ),
    longitude: float | None = Query(
        None,
        ge=-180,
        le=180
    ),
    radius_km: float | None = Query(
        None,
        gt=0,
        le=1000
    ),
    limit: int = Query(
        50,
        ge=1,
        le=200
    )
):
    """
    Get active official NDMA SACHET alerts.

    Coordinates are optional.
    If latitude and longitude are supplied,
    alerts can be filtered by radius.
    """

    if (latitude is None) != (longitude is None):
        raise HTTPException(
            status_code=400,
            detail="latitude and longitude must be supplied together"
        )

    if radius_km is not None and latitude is None:
        raise HTTPException(
            status_code=400,
            detail="radius_km requires latitude and longitude"
        )

    try:
        return get_active_official_alerts(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            limit=limit
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc)
        )