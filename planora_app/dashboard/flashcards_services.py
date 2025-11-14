# planora_app/flashcards/flashcards_services.py
from google import genai
import os
from dotenv import load_dotenv
import json

load_dotenv()
os.environ["GENAI_API_KEY"] = os.getenv("GEMINI_API_KEY")

# Initialize client once
client = genai.Client()

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
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
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
