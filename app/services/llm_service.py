def generate_response(message, weather):

    message = message.lower()

    temperature = weather.get("temperature", 0)
    feels_like = weather.get("feels_like", 0)
    humidity = weather.get("humidity", 0)
    wind = weather.get("wind_speed", 0)
    cloud = weather.get("cloud_cover", 0)

    daily = weather.get("daily", {})
    hourly = weather.get("hourly", {})

    rain_probability = 0

    if hourly.get("precipitation_probability"):
        rain_probability = hourly["precipitation_probability"][0]

    daily_rain_probability = 0

    if daily.get("precipitation_probability_max"):
        daily_rain_probability = daily["precipitation_probability_max"][0]

    max_temp = 0
    min_temp = 0

    if daily.get("temperature_2m_max"):
        max_temp = daily["temperature_2m_max"][0]

    if daily.get("temperature_2m_min"):
        min_temp = daily["temperature_2m_min"][0]


    if "temperature" in message:
        return f"The current temperature is {temperature}°C."


    if "feels" in message:
        return f"It currently feels like {feels_like}°C."

    if "rain" in message or "umbrella" in message:
      if  rain_probability >= 70:
        return f"There is a high chance of rain in the next hour, around {rain_probability}%. Carry an umbrella."

      elif rain_probability >= 40:
        return f"There is a moderate chance of rain in the next hour, around {rain_probability}%."

      else:
        return f"The chance of rain in the next hour is low, around {rain_probability}%."
   

    if "humidity" in message:
        return f"The current humidity is {humidity}%."


    if "wind" in message:
        return f"The current wind speed is {wind} km/h."


    if "cloud" in message:
        return f"Cloud cover is currently {cloud}%."


    if "hot" in message:

        if temperature >= 35:
            return f"Yes, it is quite hot at {temperature}°C. Stay hydrated and avoid unnecessary outdoor activity."

        return f"The temperature is {temperature}°C, so it is not extremely hot."


    if "cold" in message:

        if temperature <= 20:
            return f"It is relatively cool at {temperature}°C."

        return f"The temperature is {temperature}°C, so it is not particularly cold."

    if "today" in message or "forecast" in message or "weather" in message:
     return  (
        f"Today's weather is {temperature}°C with "
        f"{humidity}% humidity. "
        f"The expected temperature range is "
        f"{min_temp}°C to {max_temp}°C. "
        f"The maximum rain probability today is "
        f"{daily_rain_probability}%."
    )


    if "travel" in message or "safe" in message:

        if rain_probability >= 70:
            return "Travel may be affected by the high chance of rain. Please check the latest conditions before travelling."

        return "Current weather conditions appear generally suitable for travel."


    if "agriculture" in message or "crop" in message:

        return (
            f"For agriculture, the current temperature is {temperature}°C, "
            f"humidity is {humidity}%, and rain probability is "
            f"{rain_probability}%. Monitor your crop according to these conditions."
        )


    if "alert" in message or "warning" in message:

        if rain_probability >= 70:
            return "Weather alert: high probability of rain today."

        if temperature >= 35:
            return "Weather alert: high temperature conditions."

        if wind >= 40:
            return "Weather alert: strong winds are possible."

        return "There are no major weather risks detected by the current application rules."


    return (
        f"Current weather: {temperature}°C, "
        f"humidity {humidity}%, "
        f"wind {wind} km/h, "
        f"rain probability {rain_probability}%."
    )


def translate_response(text, language):

    translations = {

        "tamil": {
            "The current temperature is": "தற்போதைய வெப்பநிலை",
            "The current humidity is": "தற்போதைய ஈரப்பதம்",
            "The current wind speed is": "தற்போதைய காற்றின் வேகம்",
            "There is a high chance of rain today": "இன்று மழை பெய்ய அதிக வாய்ப்பு உள்ளது",
            "There is a moderate chance of rain today": "இன்று மிதமான மழை வாய்ப்பு உள்ளது",
            "The chance of rain is low today": "இன்று மழை பெய்ய வாய்ப்பு குறைவு"
        },

        "hindi": {
            "The current temperature is": "वर्तमान तापमान",
            "The current humidity is": "वर्तमान आर्द्रता",
            "The current wind speed is": "वर्तमान हवा की गति",
            "There is a high chance of rain today": "आज बारिश की अधिक संभावना है",
            "There is a moderate chance of rain today": "आज बारिश की मध्यम संभावना है",
            "The chance of rain is low today": "आज बारिश की संभावना कम है"
        },

        "telugu": {
            "The current temperature is": "ప్రస్తుత ఉష్ణోగ్రత",
            "The current humidity is": "ప్రస్తుత తేమ",
            "The current wind speed is": "ప్రస్తుత గాలి వేగం",
            "There is a high chance of rain today": "ఈరోజు వర్షం పడే అవకాశం ఎక్కువగా ఉంది",
            "There is a moderate chance of rain today": "ఈరోజు వర్షం పడే అవకాశం మధ్యస్థంగా ఉంది",
            "The chance of rain is low today": "ఈరోజు వర్షం పడే అవకాశం తక్కువగా ఉంది"
        },

        "kannada": {
            "The current temperature is": "ಪ್ರಸ್ತುತ ತಾಪಮಾನ",
            "The current humidity is": "ಪ್ರಸ್ತುತ ಆರ್ದ್ರತೆ",
            "The current wind speed is": "ಪ್ರಸ್ತುತ ಗಾಳಿಯ ವೇಗ",
            "There is a high chance of rain today": "ಇಂದು ಮಳೆಯಾಗುವ ಸಾಧ್ಯತೆ ಹೆಚ್ಚು",
            "There is a moderate chance of rain today": "ಇಂದು ಮಳೆಯಾಗುವ ಮಧ್ಯಮ ಸಾಧ್ಯತೆ ಇದೆ",
            "The chance of rain is low today": "ಇಂದು ಮಳೆಯಾಗುವ ಸಾಧ್ಯತೆ ಕಡಿಮೆ"
        },

        "malayalam": {
            "The current temperature is": "നിലവിലെ താപനില",
            "The current humidity is": "നിലവിലെ ഈർപ്പം",
            "The current wind speed is": "നിലവിലെ കാറ്റിന്റെ വേഗത",
            "There is a high chance of rain today": "ഇന്ന് മഴയ്ക്ക് ഉയർന്ന സാധ്യതയുണ്ട്",
            "There is a moderate chance of rain today": "ഇന്ന് മിതമായ മഴയ്ക്ക് സാധ്യതയുണ്ട്",
            "The chance of rain is low today": "ഇന്ന് മഴയ്ക്ക് സാധ്യത കുറവാണ്"
        },

        "bengali": {
            "The current temperature is": "বর্তমান তাপমাত্রা",
            "The current humidity is": "বর্তমান আর্দ্রতা",
            "The current wind speed is": "বর্তমান বাতাসের গতি",
            "There is a high chance of rain today": "আজ বৃষ্টির সম্ভাবনা বেশি",
            "There is a moderate chance of rain today": "আজ মাঝারি বৃষ্টির সম্ভাবনা রয়েছে",
            "The chance of rain is low today": "আজ বৃষ্টির সম্ভাবনা কম"
        }

    }


    if language == "english":
        return text


    if language not in translations:
        return text


    result = text

    for english, translated in translations[language].items():

        result = result.replace(
            english,
            translated
        )

    return result