from fastapi import APIRouter
import speech_recognition as sr

router = APIRouter(prefix="/speech", tags=["Speech"])


@router.get("/listen")
def listen_for_speech():

    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:

            print("🎤 Listening...")

            recognizer.adjust_for_ambient_noise(
                source,
                duration=1
            )

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=10
            )

        text = recognizer.recognize_google(audio)

        print("You said:", text)

        return {
            "success": True,
            "text": text
        }

    except sr.WaitTimeoutError:

        return {
            "success": False,
            "message": "No speech detected."
        }

    except sr.UnknownValueError:

        return {
            "success": False,
            "message": "Could not understand the speech."
        }

    except sr.RequestError as error:

        return {
            "success": False,
            "message": f"Speech service error: {error}"
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error)
        }