from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.weather import router as weather_router
from app.api.chatbot import router as chatbot_router
from app.api.alerts import router as alerts_router
from app.api.location import router as location_router
from app.api.agriculture import router as agriculture_router
from app.api.speech import router as speech_router
app = FastAPI(
    title="WeatherGPT India",
    description="AI-powered weather application for India",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(weather_router)
app.include_router(chatbot_router)
app.include_router(auth_router)
app.include_router(alerts_router)
app.include_router(location_router)
app.include_router(agriculture_router)
app.include_router(speech_router)

@app.get("/")
def home():
    return {
        "message": "Welcome to WeatherGPT India!"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }