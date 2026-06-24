from pathlib import Path
import os

ALLOWED_EXTENSIONS = {".pdf"}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_PDF_PAGES = 100


def allowed_file(filename):

    extension = Path(filename).suffix.lower()

    return extension in ALLOWED_EXTENSIONS


def validate_file_size(file):

    file.seek(0, os.SEEK_END)

    size = file.tell()

    file.seek(0)

    return size <= MAX_FILE_SIZE