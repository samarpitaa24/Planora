from bson import ObjectId
from datetime import datetime, UTC

from planora_app.extensions import get_db
from planora_app.ai.pdf_utils import extract_pdf_text
from planora_app.ai.chunking import chunk_text
from planora_app.ai.gemini import generate_response


def generate_mindmap(document_id):
    if not document_id or not ObjectId.is_valid(document_id):
        return None
    db = get_db()
    try:
        document = db.chat_documents.find_one({"_id": ObjectId(document_id)})
    except Exception:
        return None
    if not document:
        return None

    pdf_path = ("planora_app/static/uploads/pdfs/" + document["stored_filename"])
    text, _ = extract_pdf_text(pdf_path)
    context = "\n\n".join(chunk_text(text)[:2])
    
    prompt = f"""
You are an expert study assistant.

Generate ONE study mindmap from the provided study material.

IMPORTANT:

Return ONLY valid Mermaid mindmap syntax.

Do NOT return:
- markdown fences
- ```mermaid
- explanations
- notes
- bullet points
- numbered lists
- comments
- introductory text
- concluding text

OUTPUT RULES:

1. First line MUST be:
mindmap

2. Second line MUST be:
  root((Main Topic))

3. Use indentation with exactly two spaces per level.

4. Maximum depth:
Root → Topic → Subtopic → Detail
(4 levels only)

5. Maximum 5 children for any node.

6. Every node label must be concise:
- 1 to 4 words only
- No sentences
- No punctuation except spaces
- No brackets except root((...))

7. Merge duplicate concepts into a single branch.

8. Include ONLY the 15–20 most important concepts from the study material.
    Merge related ideas into one branch instead of creating separate branches.
    Prefer abstraction over exhaustive listing.

9. Preserve logical hierarchy.

10. If multiple topics exist, group similar concepts together.

VALID EXAMPLE:

mindmap
  root((Machine Learning))
    Supervised
      Regression
      Classification
    Unsupervised
      Clustering
      Dimensional Reduction
    Evaluation
      Accuracy
      Precision

Study Material:

{context}
"""

    try:
        response = generate_response(prompt)
        mindmap = response.strip()
        
        if mindmap.startswith("```mermaid"):
            mindmap = mindmap.replace("```mermaid","",1)

        if mindmap.startswith("```"):
            mindmap = mindmap.replace("```","",1)

        if mindmap.endswith("```"):
            mindmap = mindmap[:-3]

        mindmap = mindmap.strip()

    except Exception:
        mindmap = ""

    if len(mindmap) == 0:
        return None

    result = db.mindmaps.insert_one({
        "document_id": document_id,
        "title": document["original_filename"].replace(".pdf",""),
        "mindmap": mindmap,
        "created_at": datetime.now(UTC)})

    return {
        "id": str(result.inserted_id),
        "title": document["original_filename"].replace(".pdf","")}


def get_mindmaps():
    db = get_db()
    maps = list(db.mindmaps.find().sort("created_at",-1))
    result = []
    for item in maps:
        result.append({"id": str(item["_id"]),"title": item["title"],"created_at": item["created_at"]})

    return result


def get_mindmap(map_id):
    if not map_id or not ObjectId.is_valid(map_id):
        return None
    db = get_db()
    try:
        mindmap = db.mindmaps.find_one({"_id": ObjectId(map_id)})
    except Exception:
        return None
    if not mindmap:
        return None
    mindmap["_id"] = str(mindmap["_id"])
    return mindmap


def delete_mindmap(map_id):
    if not map_id or not ObjectId.is_valid(map_id):
        return False
    db = get_db()
    try:
        db.mindmaps.delete_one({"_id": ObjectId(map_id)})
    except Exception:
        return False
    return True

# prompt = f"""
# You are an expert study assistant.

# Generate ONE high-quality revision mindmap from the provided study material.

# Return ONLY valid Mermaid mindmap syntax.

# DO NOT return:
# - markdown fences
# - ```mermaid
# - explanations
# - notes
# - bullet points
# - numbered lists
# - comments
# - introductory text
# - concluding text

# FORMAT RULES

# 1. The first line MUST be:
# mindmap

# 2. The second line MUST be:
# root((Main Topic))

# 3. Use exactly two spaces for every indentation level.

# 4. Maximum depth:
# Root → Topic → Subtopic → Key Point
# (4 levels maximum)

# 5. Each parent should have approximately 3–6 children whenever applicable.

# 6. Every node must contain concise revision keywords:
# - 1 to 4 words
# - No full sentences
# - No unnecessary punctuation
# - Use noun phrases whenever possible

# 7. Merge duplicate concepts into one branch.

# 8. Include ALL major concepts required for exam revision.
# Do NOT omit important topics simply to reduce size.

# 9. Prefer hierarchy over long flat lists.

# 10. Group closely related concepts together.

# 11. Include:
# - definitions
# - components
# - types
# - architecture
# - steps
# - algorithms
# - advantages
# - disadvantages
# - applications
# only when they are important to understanding the topic.

# 12. Do NOT include examples unless they represent a major concept.

# 13. The final mindmap should be balanced:
# - approximately 25–40 nodes
# - readable on one screen for an average study topic
# - detailed enough for quick revision
# - not excessively dense

# VALID EXAMPLE

# mindmap
#   root((Machine Learning))
#     Supervised
#       Regression
#       Classification
#     Unsupervised
#       Clustering
#       Dimensional Reduction
#     Evaluation
#       Accuracy
#       Precision
#     Applications
#       Vision
#       NLP

# Study Material:

# {context}
# """