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
    """
    Calls Gemini API to summarize text into 5-10 concise flashcards.
    Returns a list of dictionaries with 'text' for each flashcard.
    """
    prompt = (f""" You are an expert at creating educational flashcards. Generate concise, high-quality flashcards from the text below. Follow these rules:

        1. Types of flashcards:
        - Concept card: Front shows a concept/term/title, back shows definition, explanation, formula, example, or key details.
        - Question card: Front shows a question testing active recall, back shows answer, explanation, formula, or example.

        2. Rules:
        - Each card must be self-contained. Reading front and back alone should allow learning and recall.
        - Prioritize key concepts, definitions, formulas, rules, examples, cause-effect, and comparisons.
        - Keep each card concise but complete; allow up to 50 words on back if needed.
        - Include simplified examples or mnemonics when helpful.
        - Avoid trivial or irrelevant details.
        - Generate at least one card per significant concept or section in the text.

        3. Response format (strict JSON):
            [
            {
                "type": "concept",   // "concept" or "question"
                "front": "Concept or question text",
                "back": "Definition, explanation, formula, example, or answer"
            },
            ...
            ]

        4. Always provide output in valid JSON following this format. Do not include extra commentary, numbering, preambles, or markdown symbols.

        Text:{text} """)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        raw_text = response.text

        # Directly parse the JSON output
        try:
            flashcards = json.loads(raw_text)
        except json.JSONDecodeError:
            # Fallback if Gemini returns invalid JSON
            print("[Flashcards Service] JSON parse error, returning fallback")
            flashcards = [{"type": "concept", "front": "Error", "back": "Could not parse flashcards"}]

        # Limit to max 10 cards
        flashcards = flashcards[:10]

        return flashcards

    except Exception as e:
        print(f"[Flashcards Service Error] {e}")
        return [{"type": "concept", "front": "Error", "back": "Error generating flashcards"}]