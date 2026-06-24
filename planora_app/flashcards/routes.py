from flask import Blueprint, render_template, request, jsonify
from planora_app.flashcards.services import (
    generate_flashcards,
    get_flashcard_sets,
    get_flashcard_set,
    delete_flashcard_set
)
from planora_app.chatbot.services import save_message

flashcards_bp = Blueprint(
    "flashcards",
    __name__,
    url_prefix="/flashcards"
)

@flashcards_bp.route("/")
def flashcards():

    set_id = request.args.get("set")

    conversation_id = request.args.get("conversation")

    return render_template(

        "flashcards.html",

        selected_set=set_id,

        conversation_id=conversation_id

    )


@flashcards_bp.route("/selected")
def selected_flashcards():

    set_id = request.args.get("set")

    if not set_id:

        return jsonify({
            "error": "Missing set id"
        }), 400

    flashcards = get_flashcard_set(set_id)

    if flashcards is None:

        return jsonify({
            "error": "Flashcards not found"
        }), 404

    return jsonify(flashcards)


@flashcards_bp.route("/generate", methods=["POST"])
def generate():

    data = request.get_json()

    document_id = data.get("document_id")
    card_count = data.get("card_count", 10)
    conversation_id = data.get("conversation_id")

    if not document_id:

        return jsonify({

            "error": "Document missing"

        }), 400

    flashcard_set = generate_flashcards(

        document_id,

        card_count

    )

    if flashcard_set is None:

        return jsonify({

            "success": False,

            "error": "Unable to generate flashcards."

        })

    if conversation_id:

        save_message(

            conversation_id,

            "assistant",

            "",

            message_type="flashcards",

            tool_id=flashcard_set["id"],

            tool_title=flashcard_set["title"]

        )

    return jsonify({

        "success": True,

        "flashcard_set": flashcard_set

    })
    
@flashcards_bp.route("/history")
def history():

    return jsonify(
        get_flashcard_sets()
    )


@flashcards_bp.route("/set/<set_id>")
def load_set(set_id):

    flashcards = get_flashcard_set(set_id)

    if flashcards is None:
        return jsonify({
            "error": "Not found"
        }), 404

    return jsonify(flashcards)

@flashcards_bp.route("/delete/<set_id>", methods=["DELETE"])
def delete_set(set_id):

    delete_flashcard_set(set_id)

    return jsonify({
        "success": True
    })