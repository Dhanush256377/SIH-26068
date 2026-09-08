
import os
from typing import Optional

from google import genai
from groq import Groq

from .config import GEMINI_API_KEY, GROQ_API_KEY


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------

GEMINI_MODEL = "gemini-3.8-flash"
GROQ_MODEL = "openai/gpt-oss-20b"


# ------------------------------------------------------------------
# System prompt
# ------------------------------------------------------------------

SYSTEM_PROMPT = """
You are WeatherGPT, the single AI assistant for a weather website in India.

Use the weather information supplied by the application as the primary source
for weather measurements and forecasts.

RULES:

1. Never invent temperature, rainfall, humidity, wind, visibility, wave height,
   cloud base, pressure, or any other measurement.

2. Clearly distinguish current observations from forecasts.

3. Never present a forecast as guaranteed.

4. Never claim 100% certainty.

5. If a required value is missing, say it is unavailable.

6. Never confuse precipitation probability with rainfall amount.

7. Never confuse wind speed with wind gusts.

8. Answer in the exact language requested by the user.

Supported languages:
English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali and Marathi.

9. For dangerous weather, recommend checking official meteorological alerts.

10. Agriculture:
consider crop, growth stage, rainfall, humidity, temperature, wind,
irrigation and weather-related disease pressure.

Do not diagnose plant disease from weather data alone.

11. Travel and outdoor work:
consider rain, thunderstorms, visibility, wind, heat and timing.

12. Aviation:
never give flight clearance.

Use only available aviation-relevant observations such as visibility,
wind, gusts, cloud base and thunderstorms.

13. Marine:
never invent wave height or sea-state information.

14. Answer the user's actual question first.

15. Keep answers practical and concise.

16. The structured weather data provided by the application is authoritative.
Do not replace it with guessed or remembered weather data.
""".strip()


# ------------------------------------------------------------------
# API clients
# ------------------------------------------------------------------

gemini_client = None
groq_client = None


def _clean_key(value) -> str:
    """Safely clean an environment/config value."""

    if value is None:
        return ""

    return str(value).strip()


GEMINI_API_KEY = _clean_key(GEMINI_API_KEY)
GROQ_API_KEY = _clean_key(GROQ_API_KEY)


# Gemini
if GEMINI_API_KEY:

    try:

        gemini_client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        print("WeatherGPT: Gemini client initialized.")

    except Exception as exc:

        print(
            "WeatherGPT: Gemini initialization failed: "
            f"{type(exc).__name__}: {exc}"
        )

        gemini_client = None

else:

    print(
        "WeatherGPT: GEMINI_API_KEY is not configured."
    )


# Groq
if GROQ_API_KEY:

    try:

        groq_client = Groq(
            api_key=GROQ_API_KEY
        )

        print("WeatherGPT: Groq client initialized.")

    except Exception as exc:

        print(
            "WeatherGPT: Groq initialization failed: "
            f"{type(exc).__name__}: {exc}"
        )

        groq_client = None

else:

    print(
        "WeatherGPT: GROQ_API_KEY is not configured."
    )


# ------------------------------------------------------------------
# Gemini
# ------------------------------------------------------------------

def ask_gemini(prompt: str) -> Optional[str]:

    if not gemini_client:
        return None

    try:

        interaction = gemini_client.interactions.create(

            model=GEMINI_MODEL,

            system_instruction=SYSTEM_PROMPT,

            input=prompt,

            generation_config={
                "temperature": 0.2,
                "thinking_level": "low",
            },
        )

        text = getattr(
            interaction,
            "output_text",
            None
        )

        if text:

            answer = str(text).strip()

            if answer:
                return answer

        print(
            "WeatherGPT: Gemini returned no text."
        )

        return None

    except Exception as exc:

        print(
            "WeatherGPT Gemini ERROR: "
            f"{type(exc).__name__}: {exc}"
        )

        return None


# ------------------------------------------------------------------
# Groq
# ------------------------------------------------------------------

def ask_groq(prompt: str) -> Optional[str]:

    if not groq_client:
        return None

    try:

        response = groq_client.chat.completions.create(

            model=GROQ_MODEL,

            messages=[

                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },

                {
                    "role": "user",
                    "content": prompt,
                },
            ],

            temperature=0.2,

            max_completion_tokens=2048,
        )

        if not response.choices:
            print(
                "WeatherGPT: Groq returned no choices."
            )
            return None

        message = response.choices[0].message

        text = getattr(
            message,
            "content",
            None
        )

        if text:

            answer = str(text).strip()

            if answer:
                return answer

        print(
            "WeatherGPT: Groq returned empty text."
        )

        return None

    except Exception as exc:

        print(
            "WeatherGPT Groq ERROR: "
            f"{type(exc).__name__}: {exc}"
        )

        return None


# ------------------------------------------------------------------
# Main provider
# ------------------------------------------------------------------

def ask_ai(prompt: str) -> str:

    if not prompt or not str(prompt).strip():

        raise RuntimeError(
            "AI request was empty."
        )


    provider_errors = []


    # --------------------------------------------------------------
    # Gemini first
    # --------------------------------------------------------------

    if gemini_client:

        answer = ask_gemini(
            str(prompt)
        )

        if answer:
            return answer

        provider_errors.append(
            "Gemini failed"
        )

    else:

        provider_errors.append(
            "Gemini is not configured"
        )


    # --------------------------------------------------------------
    # Groq fallback
    # --------------------------------------------------------------

    if groq_client:

        answer = ask_groq(
            str(prompt)
        )

        if answer:
            return answer

        provider_errors.append(
            "Groq failed"
        )

    else:

        provider_errors.append(
            "Groq is not configured"
        )


    # --------------------------------------------------------------
    # Nothing worked
    # --------------------------------------------------------------

    raise RuntimeError(
        "WeatherGPT AI unavailable. "
        + "; ".join(provider_errors)
        + ". Check the API keys and installed SDK versions."
    )
