# planora_app/flashcards/flashcards_routes.py
from flask import Blueprint, request, jsonify, session  # ✅ added session here
from planora_app.utils import check_and_update_quota
from .flashcards_services import generate_flashcards

flashcards_bp = Blueprint("flashcards", __name__, url_prefix="/flashcards")

# Example: adjust based on average words allowed per upload
TOKENS_PER_UPLOAD = 50

@flashcards_bp.route("/upload", methods=["POST"])
def upload_doc():
    """
    Handles file uploads (PDF, DOCX, TXT) and generates flashcards.
    Uses user session for quota tracking.
    """
    from PyPDF2 import PdfReader
    import docx
    import io

    # ✅ Use session to get logged-in user
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "File is required"}), 400

    # ✅ Check and update daily quota
    TOKENS_PER_UPLOAD = 50
    if not check_and_update_quota(user_id, TOKENS_PER_UPLOAD):
        print(f"❌ Quota exceeded for user: {user_id}")
        return jsonify({"error": "Daily token quota exceeded!"}), 403

    # ✅ Parse document content (PDF, DOCX, TXT)
    filename = file.filename.lower()
    text = ""

    try:
        if filename.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(file.read()))
            text = " ".join(page.extract_text() or "" for page in reader.pages)

        elif filename.endswith(".docx"):
            doc = docx.Document(io.BytesIO(file.read()))
            text = " ".join(p.text for p in doc.paragraphs)

        elif filename.endswith(".txt"):
            text = file.read().decode("utf-8", errors="ignore")

        else:
            return jsonify({"error": "Unsupported file format"}), 400

    except Exception as e:
        print(f"❌ Error parsing file: {e}")
        return jsonify({"error": "Failed to read the file. Please check the file content and try again."}), 500

    word_count = len(text.split())
    print(f"📎 Upload initiated by user: {user_id}")
    print(f"📄 Parsed {word_count} words from document.")

    # ✅ Generate flashcards (safe with AI overload handling)
    try:
        flashcards = generate_flashcards(user_id, text)
        return jsonify({"flashcards": flashcards})

    except Exception as e:
        print(f"[Flashcards Service Error] {e}")

        if "503" in str(e) or "UNAVAILABLE" in str(e):
            user_message = "⚠️ The flashcard generator is currently busy. Please try again later."
        elif "429" in str(e):
            user_message = "⚠️ Too many requests — please wait a moment and retry."
        else:
            user_message = "⚠️ Something went wrong while generating flashcards. Please try again."

        return jsonify({"error": user_message}), 503
