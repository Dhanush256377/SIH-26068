import speech_recognition as sr
import pyttsx3


def listen():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)

        try:
            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=10
            )

            text = recognizer.recognize_google(audio)

            print("You said:", text)

            return text

        except sr.WaitTimeoutError:
            print("No speech detected.")
            return ""

        except sr.UnknownValueError:
            print("Could not understand the speech.")
            return ""

        except sr.RequestError as error:
            print("Speech service error:", error)
            return ""


def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


if __name__ == "__main__":
    print("WeatherGPT Voice Test")

    text = listen()

    if text:
        speak("You said " + text)