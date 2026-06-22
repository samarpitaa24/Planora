"""
PDF utility functions.

Handles:
- validation
- saving pdf
- extracting text
- page count
"""

import os
import uuid
import fitz


UPLOAD_FOLDER = (
    "planora_app/static/uploads/pdfs"
)

MAX_FILE_SIZE = 10 * 1024 * 1024      # 10 MB

MAX_PAGES = 100

ALLOWED_EXTENSIONS = {
    "pdf"
}

def allowed_file(filename):

    if "." not in filename:
        return False

    extension = (
        filename
        .rsplit(".", 1)[1]
        .lower()
    )

    return extension in ALLOWED_EXTENSIONS


def save_pdf(file):

    os.makedirs(
        UPLOAD_FOLDER,
        exist_ok=True
    )

    unique_name = (
        f"{uuid.uuid4()}.pdf"
    )

    save_path = os.path.join(
        UPLOAD_FOLDER,
        unique_name
    )

    file.save(save_path)

    return (
        unique_name,
        save_path
    )


def extract_pdf_text(pdf_path):

    document = fitz.open(pdf_path)

    page_count = len(document)

    if page_count > MAX_PAGES:

        document.close()

        raise ValueError(
            "PDF exceeds maximum page limit."
        )

    extracted_text = ""

    for page in document:

        extracted_text += (
            page.get_text()
            + "\n"
        )

    document.close()

    return (
        extracted_text,
        page_count
    )
    
