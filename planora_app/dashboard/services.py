# dashboard/services.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Resolve env path from project root or planora_app/env
env_paths = [
    os.path.join(os.path.dirname(__file__), '../../.env'),
    os.path.join(os.path.dirname(__file__), '../env'),
]
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
        break

# Try GEMINI_API_KEY first, then GOOGLE_API_KEY
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

async def call_gemini_api(prompt: str) -> str:
    """
    Call Gemini 2.5 Flash via official client and return the bot response.
    """
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"(Gemini API error: {e})"
