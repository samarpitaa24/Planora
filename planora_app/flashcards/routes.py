# flashcards/routes.py

from flask import Blueprint, render_template

flashcards_bp = Blueprint(
    "flashcards",
    __name__,
    url_prefix="/flashcards"
)

@flashcards_bp.route("/")
def flashcards():
    return render_template("flashcards.html")