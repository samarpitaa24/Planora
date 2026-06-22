import os

from google import genai
from dotenv import load_dotenv

load_dotenv()

# print("=" * 60)
# print("API KEY:", os.getenv("GEMINI_API_KEY"))
# print("=" * 60)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_response(prompt):

    response = client.models.generate_content(

        model="gemini-2.5-flash",

        contents=prompt

    )

    if hasattr(response, "text"):

        return response.text

    return "I couldn't generate a response."