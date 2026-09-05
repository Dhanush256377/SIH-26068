from fastapi import APIRouter
from app.services.location_service import get_location, search_location

router = APIRouter(
    prefix="/location",
    tags=["Location"]
)


@router.get("/")
def location(latitude: float, longitude: float):

    return get_location(
        latitude,
        longitude
    )


@router.get("/search")
def location_search(city: str):

    return search_location(city)