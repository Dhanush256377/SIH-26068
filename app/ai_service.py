"""WeatherGPT AI provider service.

Drop-in replacement for app/ai_service.py.
Keeps the public ask_ai(prompt) function unchanged.
Gemini is tried first; Groq is used as fallback.
"""

from google import genai
from groq import Groq

from .config import GEMINI_API_KEY, GROQ_API_KEY


# Current Gemini model from Google's Gemini API documentation.
GEMINI_MODEL = "gemini-3.8-flash"
GROQ_MODEL = "openai/gpt-oss-20b"


SYSTEM_PROMPT = """
You are WeatherGPT, the single AI assistant for a weather website in India.

Use the weather information supplied by the application as the primary source
for weather measurements and forecasts.

RULES:
1. Never invent temperature, rainfall, humidity, wind, visibility, wave height,
   cloud base, pressure, or any other measurement.
2. Clearly distinguish current observations from forecasts.
3. Never present a forecast as guaranteed and never claim 100% certainty.
4. If a required value is missing, say it is unavailable.
5. Never confuse precipitation probability with rainfall amount.
6. Never confuse wind speed with wind gusts.
7. Answer in the exact language requested by the user. Supported languages:
   English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali and Marathi.
8. For dangerous weather, recommend checking official meteorological alerts.
9. Agriculture: consider crop, growth stage, rainfall, humidity, temperature,
   wind, irrigation and weather-related disease pressure. Do not diagnose plant
   disease from weather data alone.
10. Travel and outdoor work: consider rain, thunderstorms, visibility, wind,
    heat and timing.
11. Aviation: never give flight clearance. Use only available aviation-relevant
    observations such as visibility, wind, gusts, cloud base and thunderstorms.
12. Marine: never invent wave height or sea-state information.
13. Answer the user's actual question first and keep the advice practical.
""".strip()


gemini_client = None
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)


groq_client = None
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)


def ask_gemini(prompt: str):
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

        text = getattr(interaction, "output_text", None)
        if text:
            return str(text).strip()

        print("Gemini returned an empty response.")
        return None

    except Exception as exc:
        print(f"Gemini error: {type(exc).__name__}: {exc}")
        return None


def ask_groq(prompt: str):
    if not groq_client:
        return None

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_completion_tokens=2048,
        )

        text = response.choices[0].message.content
        if text:
            return str(text).strip()

        print("Groq returned an empty response.")
        return None

    except Exception as exc:
        print(f"Groq error: {type(exc).__name__}: {exc}")
        return None


def ask_ai(prompt: str):
    if not GEMINI_API_KEY and not GROQ_API_KEY:
        raise RuntimeError(
            "No AI API key configured. Set GEMINI_API_KEY or GROQ_API_KEY in .env."
        )

    answer = ask_gemini(prompt)
    if answer:
        return answer

    answer = ask_groq(prompt)
    if answer:
        return answer

    raise RuntimeError(
        "Both AI providers failed. Check API keys, SDK versions, network access, "
        "and provider quotas."
    )
