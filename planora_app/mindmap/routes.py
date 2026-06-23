from flask import Blueprint, render_template, request, jsonify

from planora_app.mindmap.services import (
    generate_mindmap,
    get_mindmaps,
    get_mindmap,
    delete_mindmap
)

from planora_app.chatbot.services import save_message


mindmap_bp = Blueprint(

    "mindmap",

    __name__,

    url_prefix="/mindmap"

)


@mindmap_bp.route("/")
def mindmap():

    map_id = request.args.get("map")

    conversation_id = request.args.get("conversation")

    return render_template(

        "mindmap.html",

        selected_map=map_id,

        conversation_id=conversation_id

    )


@mindmap_bp.route("/selected")
def selected_mindmap():

    map_id = request.args.get("map")

    if not map_id:

        return jsonify({

            "error": "Missing mindmap id"

        }), 400

    mindmap = get_mindmap(map_id)

    if mindmap is None:

        return jsonify({

            "error": "Mindmap not found"

        }), 404

    return jsonify(mindmap)


@mindmap_bp.route("/generate", methods=["POST"])
def generate():

    data = request.get_json()

    document_id = data.get("document_id")

    conversation_id = data.get("conversation_id")

    if not document_id:

        return jsonify({

            "error": "Document missing"

        }), 400

    mindmap = generate_mindmap(

        document_id

    )

    if mindmap is None:

        return jsonify({

            "success": False,

            "error": "Unable to generate mindmap."

        })

    if conversation_id:

        save_message(

            conversation_id,

            "assistant",

            "",

            message_type="mindmap",

            tool_id=mindmap["id"],

            tool_title=mindmap["title"]

        )

    return jsonify({

        "success": True,

        "mindmap": mindmap

    })


@mindmap_bp.route("/history")
def history():

    return jsonify(

        get_mindmaps()

    )


@mindmap_bp.route("/map/<map_id>")
def load_map(map_id):

    mindmap = get_mindmap(map_id)

    if mindmap is None:

        return jsonify({

            "error": "Not found"

        }), 404

    return jsonify(mindmap)


@mindmap_bp.route("/delete/<map_id>", methods=["DELETE"])
def delete_map(map_id):

    delete_mindmap(map_id)

    return jsonify({

        "success": True

    })