from bson import ObjectId
from datetime import datetime, UTC

from planora_app.extensions import get_db
from planora_app.ai.pdf_utils import extract_pdf_text
from planora_app.ai.chunking import chunk_text
from planora_app.ai.gemini import generate_response
import json


def generate_flashcards(document_id, card_count):
    if not document_id or not ObjectId.is_valid(document_id):
        return None
    db = get_db()
    try:
        document = db.chat_documents.find_one({
            "_id": ObjectId(document_id)
        })
    except Exception:
        return None

    if not document:
        return []

    pdf_path = (
        "planora_app/static/uploads/pdfs/"
        + document["stored_filename"])

    text, _ = extract_pdf_text(pdf_path)
    context = "\n\n".join(chunk_text(text)[:3])

    prompt = f"""
        Generate exactly {card_count} study flashcards.
        Return ONLY valid JSON.
        Format:
        [
            {{
                "front":"Question",
                "back":"Answer"
            }}
        ]

        Study Material:{context}
        """

    try:

        response = generate_response(prompt)

        # print("\n========== GEMINI RESPONSE ==========\n")
        # print(response)
        # print("\n=====================================\n")

        cleaned = response.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "", 1)

        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```", "", 1)

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        cards = json.loads(cleaned)

    except Exception as error:

        # print("\n========== FLASHCARD ERROR ==========\n")
        # print(error)
        # print("\n=====================================\n")

        cards = []

    if len(cards) == 0:
        return None
    
    result = db.flashcards.insert_one({
    "document_id": document_id,
    "title": document["original_filename"].replace(".pdf", ""),
    "card_count": len(cards),
    "cards": cards,
    "created_at": datetime.now(UTC)})

    return {
        "id": str(result.inserted_id),
        "title": document["original_filename"].replace(".pdf", ""),
        "card_count": len(cards)
    }

def get_flashcard_sets():

    db = get_db()

    sets = list(
        db.flashcards.find().sort("created_at", -1)
    )

    result = []

    for item in sets:

        result.append({
            "id": str(item["_id"]),
            "title": item["title"],
            "card_count": item["card_count"],
            "created_at": item["created_at"]
        })

    return result

def get_flashcard_set(set_id):
    if not set_id or not ObjectId.is_valid(set_id):
        return None
    db = get_db()
    try:
        flashcards = db.flashcards.find_one({
            "_id": ObjectId(set_id)
        })
    except Exception:
        return None

    if not flashcards:
        return None

    flashcards["_id"] = str(flashcards["_id"])

    return flashcards

def delete_flashcard_set(set_id):
    if not set_id or not ObjectId.is_valid(set_id):
        return False
    db = get_db()
    try:
        db.flashcards.delete_one({
            "_id": ObjectId(set_id)
        })
    except Exception:
        return False

    return True