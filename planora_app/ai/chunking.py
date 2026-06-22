CHUNK_SIZE = 4000


def chunk_text(text):

    chunks = []

    start = 0

    while start < len(text):

        end = start + CHUNK_SIZE

        chunks.append(

            text[start:end]

        )

        start = end

    return chunks