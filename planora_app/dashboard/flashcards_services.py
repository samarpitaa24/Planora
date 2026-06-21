# planora_app/flashcards/flashcards_services.py
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

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

def generate_flashcards(user_id: str, text: str) -> list:
    prompt = """
You are an expert at creating educational flashcards. Generate concise, high-quality flashcards from the text below. Follow these rules:

1. Types of flashcards:
- Concept card: Front shows a concept/term/title, back shows definition, explanation, formula, example, or key details.
- Question card: Front shows a question testing active recall, back shows answer, explanation, formula, or example.

2. Rules:
- Each card must be self-contained.
- Prioritize key concepts.
- Keep each card concise but complete.
- Include examples if helpful.
- Avoid irrelevant details.

3. Response format (strict JSON):
[
  {
    "type": "concept",
    "front": "Concept or question text",
    "back": "Definition, explanation, formula, example, or answer"
  }
]

4. Always provide valid JSON. No explanations, no markdown.

Text:
""" + text

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw_text = response.text

        try:
            flashcards = json.loads(raw_text)
        except:
            print("[Flashcards Service] JSON parse error, returning fallback")
            flashcards = [{"type": "concept", "front": "Error", "back": "Could not parse flashcards"}]

        return flashcards[:10]

    except Exception as e:
        print(f"[Flashcards Service Error] {e}")
        return [{"type": "concept", "front": "Error", "back": "Error generating flashcards"}]
