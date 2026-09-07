from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

import requests
import time
import threading

from math import radians, sin, cos, asin, sqrt
from io import BytesIO
from datetime import datetime, timedelta

from pydantic import BaseModel, Field


# ================================================================
# WEATHERGPT ROUTERS
# ================================================================

from app.api.nwp import router as nwp_router
from app.api.auth import router as auth_router
from app.api.weather import router as weather_router
from app.api.chatbot import router as chatbot_router
from app.api.alerts import router as alerts_router
from app.api.official_alerts import router as official_alerts_router
from app.api.location import router as location_router
from app.api.agriculture import router as agriculture_router
from app.api.speech import router as speech_router
from app.api.aviation import router as aviation_router
from app.api.marine import router as marine_router
from app.api.urban import router as urban_router


# ================================================================
# SERVICES
# ================================================================

from app.weather_service import get_current_weather
from app.ai_service import ask_ai


# ================================================================
# APPLICATION
# ================================================================

app = FastAPI(
    title="WeatherGPT India",
    description="AI-powered localized weather intelligence platform for India",
    version="2.0.0"
)


# ================================================================
# CORS
# ================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000",

        "https://weather-india-gpt.netlify.app",
        "https://weather-gpt-ashy.vercel.app",
        "https://weather-gpt-git-main-vortex-e5ae.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
# API ROUTERS
# ================================================================

app.include_router(weather_router)
app.include_router(chatbot_router)
app.include_router(auth_router)
app.include_router(nwp_router)
app.include_router(alerts_router)
app.include_router(official_alerts_router)
app.include_router(location_router)
app.include_router(agriculture_router)
app.include_router(speech_router)
app.include_router(aviation_router)
app.include_router(marine_router)
app.include_router(urban_router)


# ================================================================
# COMMON HELPERS
# ================================================================

def _number(value):
    """Safely convert a value to float."""
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """Calculate distance between two coordinates using Haversine."""

    earth_radius = 6371.0088

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        +
        cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    return (
        2
        * earth_radius
        * asin(
            sqrt(
                max(
                    0,
                    min(1, a)
                )
            )
        )
    )


# ================================================================
# WEATHER AI
# ================================================================

class WeatherAIRequest(BaseModel):
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    question: str
    language: str = "english"
    history: list[dict] = Field(default_factory=list)
    crop: str | None = None
    growth_stage: str | None = None


WEATHER_AGENT_SYSTEM = """
You are WeatherGPT, an evidence-grounded weather decision-support AI for India.

Your job is to help the user make practical decisions using the supplied weather data.

CORE RULES:

1. Answer in the exact language requested by the user.
   Supported languages include:
   English, Hindi, Tamil, Telugu, Kannada, Malayalam,
   Bengali and Marathi.

2. Use supplied weather data for numerical claims.

3. Never invent weather measurements.

4. Never assume missing measurements.

5. Clearly distinguish:
   - current observations
   - hourly forecasts
   - daily forecasts
   - historical data
   - general meteorological knowledge

6. Never present a forecast as a guarantee.

7. Never claim 100% certainty.

8. Do not confuse precipitation probability with rainfall amount.

9. Do not confuse wind speed with wind gusts.

10. Use the location timezone when discussing times.

11. If information required for a reliable answer is missing,
    say exactly what is missing.

12. For dangerous weather, advise checking official
    meteorological alerts.

13. Give the recommendation first for decision questions.

14. Keep explanations simple and practical.


AGRICULTURE:

Consider:
- crop
- growth stage
- rainfall
- humidity
- temperature
- wind
- irrigation
- weather-related disease pressure

Do not diagnose plant disease from weather alone.


TRAVEL:

Consider:
- rainfall
- thunderstorms
- visibility
- wind
- heat
- timing


OUTDOOR WORK:

Consider:
- heat
- rainfall
- lightning
- wind
- forecast changes


AVIATION:

Do not provide flight clearance.

Use:
- visibility
- wind
- gusts
- cloud information
- thunderstorms

Only when those measurements are actually available.


MARINE:

Never invent wave height or sea-state information.

If wave information is unavailable,
say so clearly.


HEALTH:

Provide general weather-related precautions only.

Do not diagnose medical conditions.


RESPONSE STYLE:

For simple factual questions:
Answer briefly.

For decision questions:

Recommendation:
Weather evidence:
Reason:
Recommended action:
Confidence:
"""


def _build_agent_weather_from_coordinates(
    latitude: float,
    longitude: float
) -> dict:

    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,

            "current": ",".join([
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "surface_pressure",
                "precipitation",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
                "weather_code",
                "cloud_cover",
            ]),

            "hourly": ",".join([
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation_probability",
                "precipitation",
                "rain",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
                "visibility",
                "cloud_cover",
                "cloud_base",
                "weather_code",
            ]),

            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "rain_sum",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "weather_code",
            ]),

            "forecast_days": 7,
            "timezone": "auto",
        },
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()
    current = data.get("current") or {}

    return {
        "city": "Selected location",
        "country": "India",

        "latitude": data.get(
            "latitude",
            latitude
        ),

        "longitude": data.get(
            "longitude",
            longitude
        ),

        "timezone": data.get("timezone"),

        "temperature":
            current.get("temperature_2m"),

        "feels_like":
            current.get("apparent_temperature"),

        "humidity":
            current.get("relative_humidity_2m"),

        "pressure":
            current.get("surface_pressure"),

        "precipitation":
            current.get("precipitation"),

        "rain":
            current.get("precipitation"),

        "wind_speed":
            current.get("wind_speed_10m"),

        "wind_direction":
            current.get("wind_direction_10m"),

        "wind_gust":
            current.get("wind_gusts_10m"),

        "weather_code":
            current.get("weather_code"),

        "cloud_cover":
            current.get("cloud_cover"),

        "hourly":
            data.get("hourly") or {},

        "daily":
            data.get("daily") or {},
    }


def _enrich_agent_weather(weather: dict) -> dict:

    latitude = _number(
        weather.get("latitude")
    )

    longitude = _number(
        weather.get("longitude")
    )

    if latitude is None or longitude is None:
        return weather

    try:
        forecast = _build_agent_weather_from_coordinates(
            latitude,
            longitude
        )
    except Exception:
        return weather

    merged = dict(weather)

    for key in (
        "timezone",
        "hourly",
        "daily",
        "weather_code",
        "wind_direction",
        "wind_gust",
        "cloud_cover",
        "precipitation",
        "rain",
    ):

        value = forecast.get(key)

        if value is not None and value != {}:
            merged[key] = value

    return merged


def build_weather_context(weather: dict) -> dict:

    return {
        "location": {
            "city": weather.get("city"),
            "country": weather.get(
                "country",
                "India"
            ),
            "latitude": weather.get("latitude"),
            "longitude": weather.get("longitude"),
            "timezone": weather.get("timezone"),
        },

        "current": {
            "temperature_c":
                weather.get("temperature"),

            "feels_like_c":
                weather.get("feels_like"),

            "humidity_pct":
                weather.get("humidity"),

            "pressure_hpa":
                weather.get("pressure"),

            "precipitation_mm":
                weather.get("precipitation"),

            "rain_mm":
                weather.get("rain"),

            "wind_speed_kmh":
                weather.get("wind_speed"),

            "wind_direction_deg":
                weather.get("wind_direction"),

            "wind_gust_kmh":
                weather.get("wind_gust"),

            "weather_code":
                weather.get("weather_code"),

            "weather":
                weather.get("weather"),

            "visibility_m":
                weather.get("visibility"),

            "cloud_cover_pct":
                weather.get("cloud_cover"),
        },

        "hourly":
            weather.get("hourly", {}),

        "daily":
            weather.get("daily", {}),

        "alerts":
            weather.get("alerts", []),
    }


def analyze_rain(hourly: dict) -> dict:

    probabilities = (
        hourly.get(
            "precipitation_probability"
        ) or []
    )

    times = (
        hourly.get("time") or []
    )

    valid = []

    for i, probability in enumerate(
        probabilities
    ):

        p = _number(probability)

        if (
            p is not None
            and i < len(times)
        ):

            valid.append({
                "time": times[i],
                "probability": p
            })

    if not valid:

        return {
            "status": "unknown",
            "message":
                "Hourly precipitation probability is unavailable."
        }

    maximum = max(
        valid,
        key=lambda item: item["probability"]
    )

    first_significant = next(
        (
            item
            for item in valid
            if item["probability"] >= 50
        ),
        None
    )

    return {
        "status": (
            "high"
            if maximum["probability"] >= 70
            else
            "moderate"
            if maximum["probability"] >= 40
            else
            "low"
        ),

        "maximum_probability_pct":
            round(maximum["probability"]),

        "peak_time":
            maximum["time"],

        "first_significant_rain":
            first_significant,
    }


def analyze_heat(weather: dict) -> dict:

    temperature = _number(
        weather.get("temperature")
    )

    if temperature is None:

        return {
            "status": "unknown",
            "temperature_c": None
        }

    return {
        "status": (
            "extreme"
            if temperature >= 40
            else
            "high"
            if temperature >= 38
            else
            "moderate"
            if temperature >= 35
            else
            "low"
        ),

        "temperature_c":
            temperature,
    }


def detect_weather_intent(
    question: str
) -> str:

    q = question.lower()

    intents = {

        "agriculture": [
            "crop",
            "farm",
            "farmer",
            "rice",
            "wheat",
            "maize",
            "cotton",
            "irrigat",
            "spray",
            "field",
        ],

        "travel": [
            "travel",
            "drive",
            "road",
            "journey",
            "trip",
            "outside",
            "outdoor",
        ],

        "aviation": [
            "flight",
            "airport",
            "aviation",
            "landing",
            "takeoff",
            "pilot",
        ],

        "marine": [
            "marine",
            "sea",
            "ocean",
            "fishing",
            "boat",
            "wave",
            "coast",
        ],

        "alerts": [
            "alert",
            "warning",
            "storm",
            "thunder",
            "danger",
            "risk",
            "emergency",
        ],

        "rain": [
            "rain",
            "raining",
            "umbrella",
            "precipitation",
        ],

        "heat": [
            "heat",
            "hot",
            "temperature",
            "cold",
            "cool",
            "humidity",
        ],
    }

    for intent, words in intents.items():

        if any(
            word in q
            for word in words
        ):
            return intent

    return "general"


# ================================================================
# WEATHER AI ENDPOINT
# ================================================================

@app.post("/api/weather-ai")
def weather_ai(
    request: WeatherAIRequest
):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question is required"
        )

    # ------------------------------------------------------------
    # Coordinates
    # ------------------------------------------------------------

    if (
        request.latitude is not None
        and request.longitude is not None
    ):

        if not (
            -90 <= request.latitude <= 90
            and
            -180 <= request.longitude <= 180
        ):

            raise HTTPException(
                status_code=400,
                detail="Invalid coordinates"
            )

        try:

            weather = (
                _build_agent_weather_from_coordinates(
                    request.latitude,
                    request.longitude
                )
            )

        except Exception as exc:

            raise HTTPException(
                status_code=502,
                detail=(
                    "Unable to retrieve weather data: "
                    f"{exc}"
                )
            )

    # ------------------------------------------------------------
    # City
    # ------------------------------------------------------------

    elif request.city:

        city = request.city.strip()

        try:

            weather = _enrich_agent_weather(
                get_current_weather(city)
            )

        except Exception as exc:

            raise HTTPException(
                status_code=502,
                detail=(
                    "Unable to retrieve weather data: "
                    f"{exc}"
                )
            )

    else:

        raise HTTPException(
            status_code=400,
            detail="City or coordinates are required"
        )

    context = build_weather_context(
        weather
    )

    rain_analysis = analyze_rain(
        context.get("hourly", {})
    )

    heat_analysis = analyze_heat(
        weather
    )

    intent = detect_weather_intent(
        question
    )

    history = (
        request.history[-8:]
        if isinstance(
            request.history,
            list
        )
        else []
    )

    prompt = f"""
{WEATHER_AGENT_SYSTEM}

USER LANGUAGE:
{request.language}

USER QUESTION:
{question}

DETECTED INTENT:
{intent}

RECENT CONVERSATION:
{history}

AGRICULTURE CONTEXT:

Crop:
{request.crop or "Not provided"}

Growth stage:
{request.growth_stage or "Not provided"}

STRUCTURED WEATHER CONTEXT:
{context}

DETERMINISTIC ANALYSIS:

Rain analysis:
{rain_analysis}

Heat analysis:
{heat_analysis}

Now answer the user's question.

Do not invent any measurement that is absent
from the structured context.
"""

    try:

        answer = ask_ai(prompt)

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=f"AI service failed: {exc}"
        )

    if not answer:

        raise HTTPException(
            status_code=503,
            detail="AI service is currently unavailable"
        )

    return {
        "success": True,

        "answer": answer,

        "intent": intent,

        "location":
            context["location"],

        "weather":
            context,

        "analysis": {
            "rain":
                rain_analysis,

            "heat":
                heat_analysis
        }
    }


# ================================================================
# UNIVERSAL PLACE SEARCH
# ================================================================

@app.get("/location/search-any")
def search_any_place(
    q: str,
    limit: int = 10
):

    query = (
        q or ""
    ).strip()

    if len(query) < 2:

        raise HTTPException(
            status_code=400,
            detail=(
                "Enter at least 2 characters "
                "for the place search."
            )
        )

    try:

        limit = max(
            1,
            min(
                int(limit or 10),
                15
            )
        )

    except (
        TypeError,
        ValueError
    ):

        limit = 10

    try:

        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query,
                "format": "jsonv2",
                "addressdetails": 1,
                "namedetails": 1,
                "limit": limit,
                "dedupe": 1,
                "extratags": 1,
            },

            headers={
                "User-Agent":
                    "WeatherGPT-India/2.0"
            },

            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Place search service unavailable: "
                f"{exc}"
            )
        )

    results = []

    for item in data or []:

        try:

            lat = float(
                item["lat"]
            )

            lon = float(
                item["lon"]
            )

        except (
            KeyError,
            TypeError,
            ValueError
        ):

            continue

        address = (
            item.get("address")
            or {}
        )

        place_type = (
            item.get("type")
            or
            item.get("addresstype")
            or
            "place"
        )

        locality = (
            address.get("city")
            or
            address.get("town")
            or
            address.get("village")
            or
            address.get("municipality")
            or
            address.get("suburb")
            or
            address.get("neighbourhood")
            or
            address.get("hamlet")
            or
            address.get("locality")
            or
            address.get("county")
            or
            address.get("state")
            or
            address.get("country")
            or
            item.get("name")
            or
            query
        )

        results.append({

            "name":
                item.get("name")
                or locality
                or query,

            "display_name":
                item.get("display_name")
                or query,

            "latitude":
                lat,

            "longitude":
                lon,

            "country":
                address.get(
                    "country"
                ) or "",

            "state":
                address.get(
                    "state"
                )
                or
                address.get(
                    "state_district"
                )
                or "",

            "district":
                address.get(
                    "county"
                )
                or
                address.get(
                    "city_district"
                )
                or "",

            "city":
                locality,

            "place_type":
                place_type.replace(
                    "_",
                    " "
                ).title(),

            "address_type":
                item.get(
                    "addresstype"
                ) or "",

            "osm_type":
                item.get(
                    "osm_type"
                ) or "",

            "osm_id":
                item.get("osm_id"),
        })

    return {
        "query": query,
        "count": len(results),
        "results": results
    }


# ================================================================
# RESEARCH WEATHER CACHE
# ================================================================

_RESEARCH_WEATHER_CACHE = {}

_RESEARCH_WEATHER_CACHE_TTL = 600

_RESEARCH_WEATHER_LOCK = (
    threading.Lock()
)

_RESEARCH_LAST_UPSTREAM_REQUEST = 0.0

_RESEARCH_UPSTREAM_MIN_INTERVAL = 0.20


_RESEARCH_DAILY_VARIABLES = [

    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "relative_humidity_2m_mean",
    "precipitation_sum",
    "rain_sum",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
    "cloud_cover_mean",
]


_RESEARCH_HOURLY_VARIABLES = [

    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "rain",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
]


def _research_cache_get(key):

    item = (
        _RESEARCH_WEATHER_CACHE.get(
            key
        )
    )

    if not item:
        return None

    created, value = item

    if (
        time.monotonic()
        - created
        > _RESEARCH_WEATHER_CACHE_TTL
    ):

        _RESEARCH_WEATHER_CACHE.pop(
            key,
            None
        )

        return None

    return value


def _research_cache_set(
    key,
    value
):

    _RESEARCH_WEATHER_CACHE[key] = (
        time.monotonic(),
        value
    )

    if len(
        _RESEARCH_WEATHER_CACHE
    ) > 100:

        oldest = min(
            _RESEARCH_WEATHER_CACHE,
            key=lambda k:
                _RESEARCH_WEATHER_CACHE[k][0]
        )

        _RESEARCH_WEATHER_CACHE.pop(
            oldest,
            None
        )


def _research_upstream_get(
    params
):

    global _RESEARCH_LAST_UPSTREAM_REQUEST

    with _RESEARCH_WEATHER_LOCK:

        wait = (
            _RESEARCH_UPSTREAM_MIN_INTERVAL
            -
            (
                time.monotonic()
                -
                _RESEARCH_LAST_UPSTREAM_REQUEST
            )
        )

        if wait > 0:
            time.sleep(wait)

        response = requests.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params=params,
            timeout=60
        )

        _RESEARCH_LAST_UPSTREAM_REQUEST = (
            time.monotonic()
        )

    return response


# ================================================================
# RESEARCH WEATHER
# ================================================================

@app.get("/research/weather")
def research_weather(
    latitude: float,
    longitude: float,
    start: str,
    end: str,
    resolution: str = "daily",
    model: str = "era5_land"
):

    if not (
        -90 <= latitude <= 90
        and
        -180 <= longitude <= 180
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid coordinates"
        )

    if resolution not in {
        "daily",
        "hourly"
    }:

        raise HTTPException(
            status_code=400,
            detail=(
                "Resolution must be daily or hourly"
            )
        )

    if model not in {
        "era5_land",
        "best_match"
    }:

        raise HTTPException(
            status_code=400,
            detail=(
                "Model must be era5_land or best_match"
            )
        )

    try:

        start_dt = datetime.strptime(
            start,
            "%Y-%m-%d"
        ).date()

        end_dt = datetime.strptime(
            end,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail=(
                "Dates must use YYYY-MM-DD format"
            )
        )

    if start_dt > end_dt:

        raise HTTPException(
            status_code=400,
            detail=(
                "Start date must not be after end date"
            )
        )

    key = (
        "research-v2-full-fields",
        round(latitude, 5),
        round(longitude, 5),
        start,
        end,
        resolution,
        model
    )

    cached = _research_cache_get(
        key
    )

    if cached is not None:

        cached_series = (
            cached.get("data", {})
            .get(
                "hourly"
                if resolution == "hourly"
                else "daily",
                {}
            )
        )

        required_fields = (
            _RESEARCH_HOURLY_VARIABLES
            if resolution == "hourly"
            else _RESEARCH_DAILY_VARIABLES
        )

        if all(
            field in cached_series
            for field in required_fields
        ):

            return {
                "cached": True,
                "source":
                    "Open-Meteo Historical Weather API",
                **cached
            }

        _RESEARCH_WEATHER_CACHE.pop(
            key,
            None
        )

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start,
        "end_date": end,
        "timezone": "auto"
    }

    if model == "era5_land":
        params["models"] = "era5_land"

    if resolution == "hourly":

        params["hourly"] = ",".join(
            _RESEARCH_HOURLY_VARIABLES
        )

    else:

        params["daily"] = ",".join(
            _RESEARCH_DAILY_VARIABLES
        )

    response = _research_upstream_get(
        params
    )

    if response.status_code == 429:

        retry_after = response.headers.get(
            "Retry-After",
            "60"
        )

        raise HTTPException(
            status_code=429,
            detail=(
                "Open-Meteo rate limit reached. "
                f"Please wait about {retry_after} seconds."
            ),
            headers={
                "Retry-After":
                    str(retry_after)
            }
        )

    if not response.ok:

        try:

            reason = response.json().get(
                "reason",
                response.text[:300]
            )

        except Exception:

            reason = response.text[:300]

        raise HTTPException(
            status_code=502,
            detail=(
                "Historical weather source failed: "
                f"{response.status_code} {reason}"
            )
        )

    try:

        data = response.json()

    except ValueError:

        raise HTTPException(
            status_code=502,
            detail=(
                "Historical weather source "
                "returned invalid JSON"
            )
        )

    if data.get("error"):

        raise HTTPException(
            status_code=502,
            detail=data.get(
                "reason",
                "Historical weather source returned an error"
            )
        )

    section = (
        "hourly"
        if resolution == "hourly"
        else "daily"
    )

    series = (
        data.get(section)
        or {}
    )

    if not series.get("time"):

        raise HTTPException(
            status_code=404,
            detail=(
                "No historical weather records "
                "were returned."
            )
        )

    # ------------------------------------------------------------
    # Repair missing daily values
    # ------------------------------------------------------------

    if resolution == "daily":

        daily_dates = (
            series.get("time")
            or []
        )

        def missing_positions(
            values
        ):

            if (
                not isinstance(
                    values,
                    list
                )
                or
                len(values)
                != len(daily_dates)
            ):

                return list(
                    range(
                        len(daily_dates)
                    )
                )

            return [
                i
                for i, value
                in enumerate(values)
                if value is None
            ]

        missing = {

            name:
                missing_positions(
                    series.get(name)
                )

            for name
            in _RESEARCH_DAILY_VARIABLES
        }

        missing = {
            key: value
            for key, value
            in missing.items()
            if value
        }

        if missing:

            fallback_params = {

                "latitude":
                    latitude,

                "longitude":
                    longitude,

                "start_date":
                    start,

                "end_date":
                    end,

                "timezone":
                    "auto",

                "daily":
                    ",".join(
                        _RESEARCH_DAILY_VARIABLES
                    ),

                "models":
                    "era5"
            }

            fallback = (
                _research_upstream_get(
                    fallback_params
                )
            )

            if fallback.ok:

                try:

                    fd = (
                        fallback.json()
                        .get("daily")
                        or {}
                    )

                    ft = (
                        fd.get("time")
                        or []
                    )

                    fmap = {
                        str(day): i
                        for i, day
                        in enumerate(ft)
                    }

                    for field, positions in (
                        missing.items()
                    ):

                        src = (
                            fd.get(field)
                            or []
                        )

                        target = (
                            series.get(field)
                        )

                        if (
                            not isinstance(
                                target,
                                list
                            )
                            or
                            len(target)
                            != len(daily_dates)
                        ):

                            target = [
                                None
                            ] * len(
                                daily_dates
                            )

                        for pos in positions:

                            j = fmap.get(
                                str(
                                    daily_dates[pos]
                                )
                            )

                            if (
                                j is not None
                                and
                                j < len(src)
                                and
                                src[j] is not None
                            ):

                                target[pos] = src[j]

                        series[field] = target

                    data["daily"] = series

                except Exception:
                    pass

        # --------------------------------------------------------
        # Rain fallback
        # --------------------------------------------------------

        rain_values = (
            series.get("rain_sum")
        )

        precip_values = (
            series.get(
                "precipitation_sum"
            )
        )

        if (
            isinstance(
                rain_values,
                list
            )
            and
            isinstance(
                precip_values,
                list
            )
        ):

            rain_values = list(
                rain_values
            )

            for i in range(
                min(
                    len(rain_values),
                    len(precip_values)
                )
            ):

                if (
                    rain_values[i] is None
                    and
                    precip_values[i] is not None
                ):

                    rain_values[i] = (
                        precip_values[i]
                    )

            series["rain_sum"] = (
                rain_values
            )

            data["daily"] = series

    value = {

        "data":
            data,

        "resolution":
            resolution,

        "start":
            start,

        "end":
            end,

        "model":
            model
    }

    _research_cache_set(
        key,
        value
    )

    return {

        "cached":
            False,

        "source":
            "Open-Meteo Historical Weather API",

        **value
    }


# ================================================================
# RESEARCH GEOCODING
# ================================================================

@app.get("/research/geocode")
def research_geocode(
    q: str
):

    query = (
        q or ""
    ).strip()

    if len(query) < 2:

        raise HTTPException(
            status_code=400,
            detail=(
                "Enter at least 2 characters "
                "for the location search."
            )
        )

    try:

        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": query,
                "count": 5,
                "language": "en",
                "format": "json"
            },
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Location search service unavailable: "
                f"{exc}"
            )
        )

    results = []

    for item in (
        data.get("results")
        or []
    ):

        try:

            results.append({

                "name":
                    item.get("name")
                    or query,

                "latitude":
                    float(
                        item["latitude"]
                    ),

                "longitude":
                    float(
                        item["longitude"]
                    ),

                "country":
                    item.get(
                        "country"
                    ) or "",

                "state":
                    item.get(
                        "admin1"
                    ) or "",

                "district":
                    item.get(
                        "admin2"
                    ) or "",

                "timezone":
                    item.get(
                        "timezone"
                    ) or ""
            })

        except (
            KeyError,
            TypeError,
            ValueError
        ):

            continue

    return {
        "query": query,
        "results": results
    }


# ================================================================
# RESEARCH PDF REPORT
# ================================================================

@app.post("/research/report")
async def research_report(
    request: Request
):

    try:

        payload = await request.json()

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload"
        )

    location = (
        payload.get("location")
        or {}
    )

    start = payload.get(
        "start",
        ""
    )

    end = payload.get(
        "end",
        ""
    )

    resolution = payload.get(
        "resolution",
        "daily"
    )

    records = (
        payload.get(
            "weather_records"
        )
        or []
    )

    events = (
        payload.get(
            "natural_events"
        )
        or []
    )

    if not records:

        raise HTTPException(
            status_code=400,
            detail=(
                "Run research analysis "
                "before downloading the PDF."
            )
        )

    place_name = location.get(
        "name",
        "Selected location"
    )

    state = location.get(
        "state",
        ""
    )

    lat = location.get(
        "latitude",
        ""
    )

    lon = location.get(
        "longitude",
        ""
    )

    temps = []
    rainfall = []

    for row in records:

        value = row.get(
            "mean_temperature",
            row.get("temperature")
        )

        try:

            if value not in (
                "",
                None
            ):

                temps.append(
                    float(value)
                )

        except (
            TypeError,
            ValueError
        ):

            pass

        value = row.get(
            "rainfall",
            row.get("precipitation")
        )

        try:

            if value not in (
                "",
                None
            ):

                rainfall.append(
                    float(value)
                )

        except (
            TypeError,
            ValueError
        ):

            pass

    avg_temp = (
        sum(temps) / len(temps)
        if temps
        else None
    )

    total_rain = (
        sum(rainfall)
        if rainfall
        else None
    )

    # ------------------------------------------------------------
    # ReportLab
    # ------------------------------------------------------------

    from reportlab.lib import colors

    from reportlab.lib.pagesizes import (
        A4,
        landscape
    )

    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle
    )

    from reportlab.lib.enums import (
        TA_CENTER
    )

    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak
    )

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=28,
        leftMargin=28,
        topMargin=28,
        bottomMargin=28,
        title="WeatherGPT Research Data Report",
        author="WeatherGPT India"
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ResearchTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=10
    )

    small = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontSize=7,
        leading=9
    )

    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=9,
        leading=11
    )

    story = [

        Paragraph(
            "WeatherGPT — Research Data Report",
            title_style
        ),

        Paragraph(
            f"<b>Location:</b> "
            f"{place_name}, {state} "
            f"({lat}, {lon}) "
            f"&nbsp;&nbsp; "
            f"<b>Period:</b> "
            f"{start} to {end} "
            f"&nbsp;&nbsp; "
            f"<b>Resolution:</b> "
            f"{resolution.title()}",
            body
        ),

        Spacer(1, 8),

        Paragraph(
            "<b>Historical data:</b> "
            "Open-Meteo Historical Weather API "
            "using ERA5-Land reanalysis.",
            small
        ),

        Spacer(1, 10)
    ]

    summary = [

        [
            "Records",
            str(len(records))
        ],

        [
            "Average temperature",
            (
                f"{avg_temp:.2f} °C"
                if avg_temp is not None
                else "N/A"
            )
        ],

        [
            "Total rainfall",
            (
                f"{total_rain:.2f} mm"
                if total_rain is not None
                else "N/A"
            )
        ],

        [
            "Reported natural events",
            str(len(events))
        ]
    ]

    summary_table = Table(
        summary,
        colWidths=[
            170,
            130
        ]
    )

    summary_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.lightgrey
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )

    story += [

        summary_table,

        Spacer(1, 12),

        Paragraph(
            "Historical Weather Data",
            styles["Heading2"]
        )
    ]

    if resolution == "daily":

        preferred = [

            "date",
            "mean_temperature",
            "max_temperature",
            "min_temperature",
            "humidity",
            "rainfall",
            "wind_speed",
            "wind_gusts",
            "cloud_cover"
        ]

    else:

        preferred = [

            "date",
            "temperature",
            "humidity",
            "precipitation",
            "rain",
            "wind_speed",
            "wind_direction",
            "wind_gusts",
            "cloud_cover"
        ]

    headers = [

        key.replace(
            "_",
            " "
        ).title()

        for key in preferred
    ]

    table_data = [
        headers
    ]

    for row in records:

        table_data.append([

            str(
                row.get(
                    key,
                    ""
                )
            )[:22]

            for key in preferred
        ])

    chunk_size = 38

    for chunk_start in range(
        0,
        len(table_data) - 1,
        chunk_size
    ):

        if chunk_start > 0:

            story.append(
                PageBreak()
            )

        chunk = (

            [table_data[0]]
            +
            table_data[
                chunk_start + 1:
                chunk_start + 1 + chunk_size
            ]
        )

        table = Table(
            chunk,
            repeatRows=1,
            colWidths=[
                70
            ]
            +
            [
                70
            ]
            * (
                len(headers) - 1
            )
        )

        table.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#e9eef5"
                    )
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.grey
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    3
                )
            ])
        )

        story.append(table)

    # ------------------------------------------------------------
    # Natural events
    # ------------------------------------------------------------

    if events:

        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "Reported Natural Events Near Location",
                styles["Heading2"]
            )
        )

        event_rows = [

            [
                "Date",
                "Category",
                "Event",
                "Distance (km)",
                "Source"
            ]
        ]

        for event in events:

            distance = event.get(
                "distance_km"
            )

            if distance is not None:

                try:

                    distance_text = (
                        f"{float(distance):.1f}"
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    distance_text = ""

            else:

                distance_text = ""

            event_rows.append([

                str(
                    event.get(
                        "date",
                        ""
                    )
                ),

                str(
                    event.get(
                        "category",
                        ""
                    )
                )[:28],

                str(
                    event.get(
                        "title",
                        ""
                    )
                )[:55],

                distance_text,

                str(
                    event.get(
                        "source_url",
                        ""
                    )
                )[:55]
            ])

        event_table = Table(
            event_rows,
            repeatRows=1,
            colWidths=[
                65,
                90,
                230,
                75,
                180
            ]
        )

        event_table.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#e9eef5"
                    )
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.grey
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    4
                )
            ])
        )

        story.append(
            event_table
        )

    story += [

        Spacer(1, 10),

        Paragraph(
            "Generated by WeatherGPT on "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M')}. "
            "For publication, retain source metadata "
            "and cite the underlying datasets.",
            small
        )
    ]

    doc.build(story)

    buffer.seek(0)

    filename = (
        f"weathergpt_research_"
        f"{start}_{end}.pdf"
    )

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        }
    )


# ================================================================
# RESEARCH DISASTER ALARM
# ================================================================

@app.get("/research/disaster-alarm")
def research_disaster_alarm(
    latitude: float,
    longitude: float,
    radius_km: float = 100.0
):

    if not (
        -90 <= latitude <= 90
        and
        -180 <= longitude <= 180
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid coordinates"
        )

    if (
        radius_km <= 0
        or
        radius_km > 1000
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Radius must be between "
                "1 and 1000 km"
            )
        )

    now = datetime.utcnow()

    start = (
        now - timedelta(days=3)
    ).strftime(
        "%Y-%m-%dT00:00:00"
    )

    end = now.strftime(
        "%Y-%m-%dT23:59:59"
    )

    url = (
        "https://www.gdacs.org/"
        "gdacsapi/api/events/geteventlist/SEARCH"
    )

    params = {

        "eventlist":
            "EQ;TC;FL;VO;WF",

        "fromdate":
            start,

        "todate":
            end,

        "alertlevel":
            "red;orange;green",

        "pagesize":
            100,

        "pagenumber":
            1
    }

    type_names = {

        "EQ":
            "Earthquake",

        "TC":
            "Tropical Cyclone",

        "FL":
            "Flood",

        "VO":
            "Volcano",

        "WF":
            "Wildfire"
    }

    events = []

    try:

        response = requests.get(
            url,
            params=params,
            timeout=12
        )

        response.raise_for_status()

        data = response.json()

        for feature in (
            data.get("features")
            or []
        ):

            properties = (
                feature.get(
                    "properties"
                )
                or {}
            )

            geometry = (
                feature.get(
                    "geometry"
                )
                or {}
            )

            coords = geometry.get(
                "coordinates"
            )

            if (
                not isinstance(
                    coords,
                    list
                )
                or
                len(coords) < 2
            ):

                continue

            try:

                event_lon = float(
                    coords[0]
                )

                event_lat = float(
                    coords[1]
                )

            except (
                TypeError,
                ValueError
            ):

                continue

            distance = calculate_distance_km(
                latitude,
                longitude,
                event_lat,
                event_lon
            )

            if distance > radius_km:
                continue

            alert = str(

                properties.get(
                    "alertlevel"
                )

                or

                properties.get(
                    "alertLevel"
                )

                or

                "green"

            ).lower()

            severity = (

                "high"
                if alert == "red"

                else

                "medium"
                if alert == "orange"

                else

                "low"
            )

            event_id = (

                properties.get(
                    "eventid"
                )

                or

                properties.get(
                    "eventId"
                )

                or

                properties.get(
                    "id"
                )

                or

                f"{event_lat},{event_lon}"
            )

            event_type = str(

                properties.get(
                    "eventtype"
                )

                or

                properties.get(
                    "eventType"
                )

                or

                ""
            ).upper()

            events.append({

                "id":
                    f"GDACS-{event_id}",

                "title":
                    properties.get(
                        "name"
                    )
                    or
                    properties.get(
                        "eventname"
                    )
                    or
                    properties.get(
                        "eventName"
                    )
                    or
                    "Natural hazard",

                "category":
                    type_names.get(
                        event_type,
                        "Natural Disaster"
                    ),

                "alert_level":
                    alert.upper(),

                "severity_class":
                    severity,

                "distance_km":
                    round(
                        distance,
                        1
                    ),

                "date":
                    str(
                        properties.get(
                            "todate"
                        )
                        or
                        properties.get(
                            "fromdate"
                        )
                        or
                        properties.get(
                            "datetime"
                        )
                        or
                        ""
                    )[:10],

                "source":
                    "GDACS",

                "source_url":
                    "https://www.gdacs.org/"
            })

    except (
        requests.RequestException,
        ValueError
    ) as exc:

        return {

            "ok": False,

            "events": [],

            "error":
                str(exc)
        }

    rank = {

        "high": 0,
        "medium": 1,
        "low": 2
    }

    events.sort(
        key=lambda event: (

            rank.get(
                event["severity_class"],
                9
            ),

            event["distance_km"]
        )
    )

    return {

        "ok":
            True,

        "checked_at":
            datetime.utcnow().isoformat()
            + "Z",

        "location": {

            "latitude":
                latitude,

            "longitude":
                longitude,

            "radius_km":
                radius_km
        },

        "events":
            events[:50],

        "official_note":
            (
                "Use official NDMA SACHET/IMD "
                "warnings for operational decisions. "
                "WeatherGPT only relays detected events."
            )
    }


# ================================================================
# RESEARCH DISASTERS
# ================================================================

@app.get("/research/disasters")
def research_disasters(
    latitude: float,
    longitude: float,
    start: str,
    end: str,
    radius_km: float = 50.0
):

    if not (
        -90 <= latitude <= 90
        and
        -180 <= longitude <= 180
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid coordinates"
        )

    if (
        radius_km <= 0
        or
        radius_km > 1000
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Radius must be between "
                "1 and 1000 km"
            )
        )

    try:

        start_dt = datetime.strptime(
            start,
            "%Y-%m-%d"
        )

        end_dt = datetime.strptime(
            end,
            "%Y-%m-%d"
        )

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail=(
                "Dates must use YYYY-MM-DD format"
            )
        )

    if start_dt > end_dt:

        raise HTTPException(
            status_code=400,
            detail=(
                "Start date must not be after "
                "end date"
            )
        )

    lat_delta = (
        radius_km / 111.32
    )

    lon_scale = max(
        0.01,
        cos(radians(latitude))
    )

    lon_delta = (
        radius_km
        /
        (111.32 * lon_scale)
    )

    min_lon = max(
        -180,
        longitude - lon_delta
    )

    max_lon = min(
        180,
        longitude + lon_delta
    )

    min_lat = max(
        -90,
        latitude - lat_delta
    )

    max_lat = min(
        90,
        latitude + lat_delta
    )

    results = []
    seen = set()

    # ------------------------------------------------------------
    # GDACS
    # ------------------------------------------------------------

    gdacs_url = (
        "https://www.gdacs.org/"
        "gdacsapi/api/events/geteventlist/SEARCH"
    )

    gdacs_types = (
        "EQ;TC;FL;VO;DR;WF"
    )

    type_names = {

        "EQ":
            "Earthquake",

        "TC":
            "Tropical Cyclone",

        "FL":
            "Flood",

        "VO":
            "Volcano",

        "DR":
            "Drought",

        "WF":
            "Wildfire"
    }

    for page in range(
        1,
        11
    ):

        params = {

            "eventlist":
                gdacs_types,

            "fromdate":
                start + "T00:00:00",

            "todate":
                end + "T23:59:59",

            "alertlevel":
                "red;orange;green",

            "pagesize":
                100,

            "pagenumber":
                page
        }

        try:

            response = requests.get(
                gdacs_url,
                params=params,
                timeout=12
            )

            response.raise_for_status()

            data = response.json()

            features = (
                data.get(
                    "features"
                )
                or []
            )

            if not features:
                break

            for feature in features:

                properties = (
                    feature.get(
                        "properties"
                    )
                    or {}
                )

                geometry = (
                    feature.get(
                        "geometry"
                    )
                    or {}
                )

                coords = geometry.get(
                    "coordinates"
                )

                if (
                    not isinstance(
                        coords,
                        list
                    )
                    or
                    len(coords) < 2
                ):

                    continue

                try:

                    event_lon = float(
                        coords[0]
                    )

                    event_lat = float(
                        coords[1]
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue

                distance = calculate_distance_km(
                    latitude,
                    longitude,
                    event_lat,
                    event_lon
                )

                if distance > radius_km:
                    continue

                event_id = (

                    properties.get(
                        "eventid"
                    )

                    or

                    properties.get(
                        "eventId"
                    )

                    or

                    properties.get(
                        "id"
                    )

                    or

                    f"{event_lat},{event_lon}"
                )

                event_type = str(

                    properties.get(
                        "eventtype"
                    )

                    or

                    properties.get(
                        "eventType"
                    )

                    or

                    ""
                ).upper()

                unique_id = (
                    f"GDACS-{event_id}-"
                    f"{event_lat}-{event_lon}"
                )

                if unique_id in seen:
                    continue

                seen.add(
                    unique_id
                )

                alert = str(

                    properties.get(
                        "alertlevel"
                    )

                    or

                    properties.get(
                        "alertLevel"
                    )

                    or

                    "unknown"
                ).lower()

                severity = (

                    "high"
                    if alert == "red"

                    else

                    "medium"
                    if alert == "orange"

                    else

                    "low"
                )

                results.append({

                    "id":
                        unique_id,

                    "title":
                        properties.get(
                            "name"
                        )
                        or
                        properties.get(
                            "eventname"
                        )
                        or
                        properties.get(
                            "eventName"
                        )
                        or
                        "GDACS disaster",

                    "description":
                        (
                            "Reported natural hazard "
                            "recorded by the Global "
                            "Disaster Alert and "
                            "Coordination System."
                        ),

                    "category":
                        type_names.get(
                            event_type,
                            "Natural Disaster"
                        ),

                    "date":
                        str(
                            properties.get(
                                "todate"
                            )
                            or
                            properties.get(
                                "fromdate"
                            )
                            or
                            properties.get(
                                "datetime"
                            )
                            or
                            ""
                        )[:10],

                    "distance_km":
                        round(
                            distance,
                            2
                        ),

                    "severity_class":
                        severity,

                    "source":
                        "GDACS",

                    "source_url":
                        "https://www.gdacs.org/"
                })

            if len(features) < 100:
                break

        except (
            requests.RequestException,
            ValueError
        ):

            break

    # ------------------------------------------------------------
    # NASA EONET
    # ------------------------------------------------------------

    eonet_url = (
        "https://eonet.gsfc.nasa.gov/"
        "api/v3/events"
    )

    eonet_params = {

        "status":
            "all",

        "start":
            start,

        "end":
            end,

        "bbox":
            f"{min_lon},{min_lat},"
            f"{max_lon},{max_lat}",

        "limit":
            500
    }

    try:

        response = requests.get(
            eonet_url,
            params=eonet_params,
            timeout=15
        )

        response.raise_for_status()

        payload = response.json()

        def geometry_points(
            geometry
        ):

            for item in geometry or []:

                geometry_type = item.get(
                    "type"
                )

                coords = item.get(
                    "coordinates"
                )

                event_date = (
                    item.get(
                        "date"
                    )
                    or
                    ""
                )

                def point(
                    coordinate
                ):

                    if (
                        isinstance(
                            coordinate,
                            list
                        )
                        and
                        len(coordinate) >= 2
                    ):

                        try:

                            return (

                                float(
                                    coordinate[1]
                                ),

                                float(
                                    coordinate[0]
                                ),

                                event_date
                            )

                        except (
                            TypeError,
                            ValueError
                        ):

                            return None

                    return None

                if geometry_type == "Point":

                    point_value = point(
                        coords
                    )

                    if point_value:
                        yield point_value

                elif geometry_type in (
                    "LineString",
                    "MultiPoint"
                ):

                    for coordinate in (
                        coords or []
                    ):

                        point_value = point(
                            coordinate
                        )

                        if point_value:
                            yield point_value

                elif geometry_type in (
                    "Polygon",
                    "MultiLineString"
                ):

                    for ring in (
                        coords or []
                    ):

                        for coordinate in (
                            ring or []
                        ):

                            point_value = point(
                                coordinate
                            )

                            if point_value:
                                yield point_value

                elif geometry_type == "MultiPolygon":

                    for polygon in (
                        coords or []
                    ):

                        for ring in (
                            polygon or []
                        ):

                            for coordinate in (
                                ring or []
                            ):

                                point_value = point(
                                    coordinate
                                )

                                if point_value:
                                    yield point_value

        for event in (
            payload.get(
                "events"
            )
            or []
        ):

            points = list(
                geometry_points(
                    event.get(
                        "geometry"
                    )
                    or []
                )
            )

            if not points:
                continue

            distance, nearest = min(

                (
                    calculate_distance_km(
                        latitude,
                        longitude,
                        point[0],
                        point[1]
                    ),

                    point
                )

                for point in points
            )

            if distance > radius_km:
                continue

            event_id = (

                event.get("id")
                or
                event.get("title")
                or
                "eonet-event"
            )

            unique_id = (
                f"EONET-{event_id}"
            )

            if unique_id in seen:
                continue

            seen.add(
                unique_id
            )

            categories = (
                event.get(
                    "categories"
                )
                or []
            )

            category = (

                categories[0].get(
                    "title",
                    "Natural Event"
                )

                if categories

                else

                "Natural Event"
            )

            title = (

                event.get(
                    "title"
                )

                or

                "Natural Event"
            ).strip()

            text = (
                f"{title} {category}"
            ).lower()

            high_words = [

                "storm",
                "cyclone",
                "hurricane",
                "typhoon",
                "flood",
                "volcano",
                "landslide",
                "wildfire",
                "fire",
                "tsunami",
                "earthquake"
            ]

            medium_words = [

                "drought",
                "dust",
                "snow",
                "ice"
            ]

            severity = (

                "high"
                if any(
                    word in text
                    for word in high_words
                )

                else

                "medium"
                if any(
                    word in text
                    for word in medium_words
                )

                else

                "low"
            )

            results.append({

                "id":
                    unique_id,

                "title":
                    title,

                "description":
                    event.get(
                        "description"
                    )
                    or
                    "",

                "category":
                    category,

                "date":
                    (
                        nearest[2]
                        or
                        event.get(
                            "closed"
                        )
                        or
                        ""
                    )[:10],

                "distance_km":
                    round(
                        distance,
                        2
                    ),

                "severity_class":
                    severity,

                "source":
                    "NASA EONET",

                "source_url":
                    event.get(
                        "link"
                    )
                    or
                    ""
            })

    except (
        requests.RequestException,
        ValueError
    ):

        pass

    results.sort(
        key=lambda item: (

            item.get(
                "date"
            )
            or
            "9999-99-99",

            item.get(
                "distance_km",
                999999
            )
        )
    )

    return {

        "source":
            "GDACS + NASA EONET",

        "radius_km":
            radius_km,

        "location": {

            "latitude":
                latitude,

            "longitude":
                longitude
        },

        "events":
            results
    }


# ==================================================================
# CROP ADVISOR (ADDITIVE FEATURE - DOES NOT REPLACE EXISTING ROUTES)
# ==================================================================

class CropAdvisorRequest(BaseModel):
    latitude: float
    longitude: float
    crop: str = "rice"
    growth_stage: str = "flowering"


# Crop thresholds are intentionally conservative. They are used only for
# weather-risk guidance, not for diagnosing disease or replacing local advice.
_CROP_PROFILES = {
    "rice": {"name": "Rice", "temp": (20, 35), "heat": 38, "cold": 15, "humidity": 80, "wet_tolerant": True, "note": "Maintain suitable soil moisture for the stage, but keep drainage available during prolonged heavy rain."},
    "wheat": {"name": "Wheat", "temp": (12, 25), "heat": 32, "cold": 5, "humidity": 70, "wet_tolerant": False, "note": "Avoid excess irrigation, especially near maturity, and watch warm humid weather during grain filling."},
    "maize": {"name": "Maize", "temp": (18, 32), "heat": 36, "cold": 10, "humidity": 70, "wet_tolerant": False, "note": "Moisture is important around flowering and grain filling, while prolonged waterlogging should be avoided."},
    "cotton": {"name": "Cotton", "temp": (21, 35), "heat": 38, "cold": 15, "humidity": 70, "wet_tolerant": False, "note": "Avoid prolonged leaf wetness during flowering and boll development and use calm, dry spray windows."},
    "groundnut": {"name": "Groundnut", "temp": (20, 30), "heat": 36, "cold": 12, "humidity": 75, "wet_tolerant": False, "note": "Good drainage is important; repeated wet periods can increase moisture-related disease pressure."},
    "sugarcane": {"name": "Sugarcane", "temp": (20, 35), "heat": 40, "cold": 12, "humidity": 80, "wet_tolerant": True, "note": "Maintain adequate moisture during active growth but prevent prolonged uncontrolled waterlogging."},
    "banana": {"name": "Banana", "temp": (20, 32), "heat": 38, "cold": 12, "humidity": 80, "wet_tolerant": True, "note": "Maintain steady moisture and drainage; strong winds can damage leaves and plants."},
    "tomato": {"name": "Tomato", "temp": (18, 30), "heat": 35, "cold": 10, "humidity": 75, "wet_tolerant": False, "note": "Wet foliage and high humidity can increase disease pressure; prefer suitable dry periods for spraying."},
    "onion": {"name": "Onion", "temp": (13, 28), "heat": 34, "cold": 5, "humidity": 70, "wet_tolerant": False, "note": "Avoid prolonged leaf wetness, particularly near bulb maturity and harvest, and provide good drainage."},
    "potato": {"name": "Potato", "temp": (15, 25), "heat": 30, "cold": 3, "humidity": 75, "wet_tolerant": False, "note": "Cool conditions are generally favorable; wet foliage and excess heat need close monitoring."},
    "soybean": {"name": "Soybean", "temp": (20, 30), "heat": 36, "cold": 10, "humidity": 75, "wet_tolerant": False, "note": "Avoid prolonged waterlogging and scout closely when humidity and wetness remain high."},
    "chickpea": {"name": "Chickpea", "temp": (15, 30), "heat": 34, "cold": 5, "humidity": 65, "wet_tolerant": False, "note": "Generally favors relatively dry conditions; wet weather around flowering and pod filling deserves attention."},
    "pigeonpea": {"name": "Pigeon Pea", "temp": (20, 32), "heat": 36, "cold": 12, "humidity": 70, "wet_tolerant": False, "note": "Avoid prolonged waterlogging and monitor flowering and pod development during wet periods."},
    "mustard": {"name": "Mustard", "temp": (10, 25), "heat": 30, "cold": 3, "humidity": 65, "wet_tolerant": False, "note": "Cool and relatively dry conditions are generally favorable; rain around flowering or harvest needs attention."},
    "millets": {"name": "Millets", "temp": (20, 35), "heat": 40, "cold": 12, "humidity": 65, "wet_tolerant": False, "note": "Generally tolerant of heat and lower rainfall, but prolonged waterlogging and rain near maturity can be harmful."},
    "vegetables": {"name": "Vegetables", "temp": (18, 32), "heat": 35, "cold": 8, "humidity": 75, "wet_tolerant": False, "note": "Requirements vary by vegetable; prioritize drainage, crop scouting and safe dry spray windows."},
}

_CROP_STAGE_NAMES = {
    "sowing": "Sowing",
    "vegetative": "Vegetative",
    "flowering": "Flowering",
    "fruiting": "Fruiting / Grain filling",
    "maturity": "Maturity",
    "harvest": "Harvest",
}


def _crop_num(value):
    try:
        number = float(value)
        return number if number == number else None
    except (TypeError, ValueError):
        return None


def _crop_hourly_values(hourly, name, limit=24):
    values = []
    for value in (hourly.get(name) or [])[:limit]:
        number = _crop_num(value)
        if number is not None:
            values.append(number)
    return values


@app.post("/api/crop-advisor")
def crop_advisor(request: CropAdvisorRequest):
    """Return deterministic crop/weather guidance from live Open-Meteo data."""
    if not (-90 <= request.latitude <= 90 and -180 <= request.longitude <= 180):
        raise HTTPException(status_code=400, detail="Invalid coordinates")

    crop_key = (request.crop or "rice").strip().lower().replace(" ", "_")
    profile = _CROP_PROFILES.get(crop_key, _CROP_PROFILES["vegetables"])
    stage = (request.growth_stage or "flowering").strip().lower()
    if stage not in _CROP_STAGE_NAMES:
        stage = "flowering"

    params = {
        "latitude": request.latitude,
        "longitude": request.longitude,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m,precipitation,weather_code",
        "hourly": "precipitation_probability,precipitation,rain,temperature_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,weather_code",
        "forecast_days": 3,
        "timezone": "auto",
    }

    try:
        response = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Live crop weather service unavailable: {exc}")
    except ValueError:
        raise HTTPException(status_code=502, detail="Live crop weather service returned invalid data")

    current = data.get("current") or {}
    hourly = data.get("hourly") or {}
    daily = data.get("daily") or {}

    temp = _crop_num(current.get("temperature_2m"))
    humidity = _crop_num(current.get("relative_humidity_2m"))
    wind = _crop_num(current.get("wind_speed_10m"))
    gust = _crop_num(current.get("wind_gusts_10m"))
    current_rain = _crop_num(current.get("precipitation")) or 0.0

    rain_probs = _crop_hourly_values(hourly, "precipitation_probability")
    rain_amounts = _crop_hourly_values(hourly, "precipitation")
    rain24_probability = max(rain_probs) if rain_probs else _crop_num((daily.get("precipitation_probability_max") or [None])[0])
    rain24_probability = rain24_probability if rain24_probability is not None else 0.0
    rain24_amount = sum(rain_amounts) if rain_amounts else current_rain

    hourly_temps = _crop_hourly_values(hourly, "temperature_2m")
    hourly_humidity = _crop_hourly_values(hourly, "relative_humidity_2m")
    hourly_wind = _crop_hourly_values(hourly, "wind_speed_10m")
    hourly_gust = _crop_hourly_values(hourly, "wind_gusts_10m")
    codes = [int(v) for v in _crop_hourly_values(hourly, "weather_code")]
    thunderstorm = any(code in (95, 96, 99) for code in codes) or int(_crop_num(current.get("weather_code")) or 0) in (95, 96, 99)

    max_temp = max(hourly_temps) if hourly_temps else temp
    min_temp = min(hourly_temps) if hourly_temps else temp
    max_humidity = max(hourly_humidity) if hourly_humidity else humidity
    max_wind = max(hourly_wind) if hourly_wind else wind
    max_gust = max(hourly_gust) if hourly_gust else gust

    risk_flags = []
    if rain24_probability >= 70 or rain24_amount >= 5:
        risk_flags.append("HIGH_RAIN")
    elif rain24_probability >= 40 or rain24_amount >= 2:
        risk_flags.append("RAIN_RISK")

    if max_temp is not None and max_temp >= profile["heat"]:
        risk_flags.append("HEAT_STRESS")
    if min_temp is not None and min_temp < profile["cold"]:
        risk_flags.append("COLD_STRESS")
    if (max_humidity is not None and max_humidity >= profile["humidity"] and
            (rain24_probability >= 40 or rain24_amount >= 2)):
        risk_flags.append("DISEASE_PRESSURE")
    if (max_wind is not None and max_wind >= 35) or (max_gust is not None and max_gust >= 45):
        risk_flags.append("WIND_RISK")
    if thunderstorm:
        risk_flags.append("THUNDERSTORM")
    if stage == "harvest" and (rain24_probability >= 50 or rain24_amount >= 5):
        risk_flags.append("HARVEST_RAIN_RISK")
    if not risk_flags:
        risk_flags.append("LOW_WEATHER_RISK")

    # Irrigation: rain comes first, then heat, then normal soil-moisture guidance.
    if rain24_probability >= 60 or rain24_amount >= 5:
        irrigation = "Postpone routine irrigation for now and check field drainage; useful rain is likely in the next 24 hours."
    elif temp is not None and temp >= profile["heat"]:
        irrigation = "Check root-zone moisture frequently and irrigate only when the crop actually needs it; prefer cooler hours."
    elif profile["wet_tolerant"]:
        irrigation = "Maintain crop-appropriate moisture, but check the soil before irrigating and avoid prolonged standing water."
    else:
        irrigation = "Irrigate only according to soil moisture and crop stage; do not irrigate automatically when useful rain is expected."

    # Spraying: never encourage spraying in rain, thunderstorm or strong wind.
    if thunderstorm or rain24_probability >= 60 or rain24_amount >= 2:
        spraying = "Avoid spraying during rain or thunderstorms. Wait for a sufficiently dry, calmer window and follow the approved product label."
    elif (wind is not None and wind >= 25) or (gust is not None and gust >= 35):
        spraying = "Postpone wind-sensitive spraying until conditions are calmer to reduce drift; follow the approved product label."
    elif humidity is not None and humidity >= 85:
        spraying = "If treatment is required, choose a dry, calm window after foliage can dry; follow the approved product label."
    else:
        spraying = "A weather window is relatively suitable for planned spraying if the crop needs treatment; follow the approved product label and local agronomic advice."

    if rain24_probability >= 70 or rain24_amount >= 5:
        rain_waterlogging = "High"
        recommendation = "Prioritize drainage and postpone weather-sensitive farm operations because significant rain is likely."
        status_class = "danger"
    elif rain24_probability >= 40 or rain24_amount >= 2:
        rain_waterlogging = "Moderate"
        recommendation = "Plan around the expected wet period and monitor field access, drainage and crop moisture."
        status_class = "warning"
    else:
        rain_waterlogging = "Low"
        recommendation = "Weather is generally suitable for routine crop monitoring; continue checking field conditions before each operation."
        status_class = "good"

    if max_temp is not None and max_temp >= profile["heat"]:
        heat_cold = f"Heat stress risk is elevated; forecast temperature may reach about {max_temp:.1f}°C."
        status_class = "danger" if max_temp >= profile["heat"] + 2 else "warning"
    elif min_temp is not None and min_temp < profile["cold"]:
        heat_cold = f"Cold stress is possible; forecast temperature may fall to about {min_temp:.1f}°C."
        status_class = "warning"
    else:
        heat_cold = "Forecast temperatures are within the crop's broad weather range."

    if max_humidity is not None and max_humidity >= profile["humidity"] and (rain24_probability >= 40 or rain24_amount >= 2):
        disease_pressure = "HIGH"
        disease_message = "High humidity plus wet-weather signals can increase moisture-driven disease pressure; scout the crop closely."
    elif (max_humidity is not None and max_humidity >= 70) or rain24_probability >= 35:
        disease_pressure = "MODERATE"
        disease_message = "Humidity or wetness is elevated; inspect leaves, stems and canopy for early symptoms."
    else:
        disease_pressure = "LOW"
        disease_message = "Current weather signals indicate lower moisture-driven disease pressure, but routine scouting is still needed."

    if (max_wind is not None and max_wind >= 35) or (max_gust is not None and max_gust >= 45):
        wind_risk = "High"
    elif (max_wind is not None and max_wind >= 25) or (max_gust is not None and max_gust >= 35):
        wind_risk = "Moderate"
    else:
        wind_risk = "Low"

    if stage == "sowing" and rain24_probability >= 70:
        stage_advice = "Sowing: heavy rain can disturb seed placement or make soil unworkable; use a workable field window."
    elif stage == "flowering":
        stage_advice = "Flowering: avoid unnecessary weather stress and protect pollination-sensitive operations from heavy rain or strong wind."
    elif stage == "fruiting":
        stage_advice = "Fruiting / grain filling: keep moisture balanced and avoid prolonged waterlogging or severe heat stress."
    elif stage == "maturity":
        stage_advice = "Maturity: monitor rain closely because wet conditions can affect crop quality, drying and harvest timing."
    elif stage == "harvest":
        stage_advice = "Harvest: prefer a workable, drier field window when possible and protect harvested produce from rain."
    else:
        stage_advice = f"{_CROP_STAGE_NAMES[stage]}: monitor soil moisture and weather changes before field operations."

    advice = {
        "irrigation": irrigation,
        "spraying": spraying,
        "rain_waterlogging": rain_waterlogging,
        "heat_cold_stress": heat_cold,
        "disease_pressure": disease_pressure,
        "wind_risk": wind_risk,
        "recommendation": recommendation,
        "stage_advice": stage_advice,
        "disease_message": disease_message,
    }

    weather_summary = {
        "temperature_c": temp,
        "humidity_pct": humidity,
        "rain_probability_pct": round(rain24_probability),
        "rain_amount_next_24h_mm": round(rain24_amount, 2),
        "wind_kmh": wind,
        "wind_gust_kmh": gust,
        "forecast_max_temperature_c": max_temp,
        "forecast_min_temperature_c": min_temp,
        "forecast_max_humidity_pct": max_humidity,
        "forecast_max_wind_kmh": max_wind,
        "forecast_max_gust_kmh": max_gust,
        "thunderstorm": thunderstorm,
    }

    return {
        "success": True,
        "crop": profile["name"],
        "growth_stage": stage,
        "growth_stage_name": _CROP_STAGE_NAMES[stage],
        "advice": advice,
        "risk_flags": risk_flags,
        "weather_summary": weather_summary,
        "crop_specific_note": profile["note"],
        "timezone": data.get("timezone"),
        "forecast": {"hourly": hourly, "daily": daily},
        "status_class": status_class,
        "location": {"latitude": request.latitude, "longitude": request.longitude},
    }

# ================================================================
# FRONTEND ROUTES
# ================================================================

@app.get("/")
def home():

    return FileResponse(
        "login.html"
    )


@app.get("/index.html")
def index_html_page():

    return FileResponse(
        "index.html"
    )


@app.get("/login")
def login_page():

    return FileResponse(
        "login.html"
    )


@app.get("/login.html")
def login_html_page():

    return FileResponse(
        "login.html"
    )


@app.get("/register")
def register_page():

    return FileResponse(
        "register.html"
    )


@app.get("/register.html")
def register_html_page():

    return FileResponse(
        "register.html"
    )


# ================================================================
# HEALTH CHECK
# ================================================================

@app.get("/health")
def health():

    return {

        "status":
            "healthy",

        "service":
            "WeatherGPT India",

        "version":
            "2.0.0",

        "ai":
            "Gemini + Groq",

        "weather":
            "OpenWeather + Open-Meteo",

        "research":
            "Open-Meteo Historical API",

        "disasters":
            "GDACS + NASA EONET"
    }