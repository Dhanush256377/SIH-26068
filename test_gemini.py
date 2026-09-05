import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

key = os.getenv("GEMINI_API_KEY")

print("Key loaded:", key is not None)

client = genai.Client(api_key=key)

response = client.models.generate_content(
   model="gemini-3.6-flash",
    contents="Say hello in one sentence."
)

print(response.text)