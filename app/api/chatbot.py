from fastapi import APIRouter

from app.services.weather_service import get_weather

from app.services.llm_service import (
    generate_response,
    translate_response
)


router = APIRouter(
    prefix="/chatbot",
    tags=["Chatbot"]
)


@router.get("/")
def chatbot(
    message: str,
    latitude: float,
    longitude: float,
    language: str = "english"
):

    weather = get_weather(
        latitude,
        longitude
    )


    if "error" in weather:

        return weather


    answer = generate_response(
        message,
        weather
    )


    answer = translate_response(
        answer,
        language
    )


    return {

        "question": message,

        "language": language,

        "answer": answer,

        "weather": weather

    }