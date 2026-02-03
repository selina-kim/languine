"""
Translation API endpoints using DeepL.
"""

from flask import Blueprint, request, Response
import json
from services.translate_service import translate_text

translate_bp = Blueprint("translate", __name__)

# POST: curl -X POST http://127.0.0.1:8080/translate -H "Content-Type: application/json" -d '{"text":"Hello","target_lang":"ES"}'
# GET: http://127.0.0.1:8080/translate?text=Hello&target=KO&source=EN
# POST used for translation requests, GET for convenience/testing
@translate_bp.route("/translate", methods=["POST", "GET"])
def translate():
    try:
        # handle POST request
        if request.method == "POST":
            data = request.get_json()
            text = data.get("text")
            target_lang = data.get("target_lang")
            source_lang = data.get("source_lang")  # optional
        # handle GET request
        else:
            text = request.args.get("text")
            target_lang = request.args.get("target")
            source_lang = request.args.get("source")  # optional

        # validate required fields
        if not text or not target_lang:
            return Response(
                json.dumps({"error": "Missing text or target_lang"}, ensure_ascii=False),
                status=400,
                mimetype="application/json; charset=utf-8"
            )

        # call translation service
        response_data = translate_text(
            text=text,
            target_lang=target_lang,
            source_lang=source_lang
        )

        # return JSON Response with UTF-8
        return Response(
            json.dumps(response_data, ensure_ascii=False),
            mimetype="application/json; charset=utf-8"
        )

    except ValueError as e:
        return Response(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            status=500,
            mimetype="application/json; charset=utf-8"
        )
    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            status=500,
            mimetype="application/json; charset=utf-8"
        )