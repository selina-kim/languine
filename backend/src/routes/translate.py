from flask import Blueprint, request, Response
import deepl, json, os
from src.services.dictionary_api import *

translate_bp = Blueprint("translate", __name__)

# test using http://127.0.0.1:8080/translate/Hello/EN/KO
# and http://127.0.0.1:8080/translate/goodbye/FR
# GET route with optional source_lang
@translate_bp.route("/translate", methods=["POST"])
@translate_bp.route("/translate/<path:text>/<target_lang>", defaults={"source_lang": None}, methods=["GET"])
@translate_bp.route("/translate/<path:text>/<source_lang>/<target_lang>", methods=["GET"])
# translate text with deepl api
def translate(text=None, source_lang=None, target_lang=None):
    try:
        # Handle POST request
        if request.method == "POST":
            data = request.get_json()
            text = data.get("text")
            target_lang = data.get("target_lang")
            source_lang = data.get("source_lang")  # optional

        # Validate required fields
        if not text or not target_lang:
            return Response(
                json.dumps({"error": "Missing text or target_lang"}, ensure_ascii=False),
                status=400,
                mimetype="application/json; charset=utf-8"
            )

        # Load DeepL API key from environment
        auth_key = os.getenv("DEEPL_API_KEY")
        if not auth_key:
            return Response(
                json.dumps({"error": "DEEPL_API_KEY not set in environment"}, ensure_ascii=False),
                status=500,
                mimetype="application/json; charset=utf-8"
            )

        deepl_client = deepl.DeepLClient(auth_key)

        # Translate with or without source_lang
        if source_lang:
            result = deepl_client.translate_text(text, source_lang=source_lang, target_lang=target_lang)
        else:
            result = deepl_client.translate_text(text, target_lang=target_lang)

        response_data = {
            "detectedSourceLang": getattr(result, "detected_source_lang", None),
            "translatedText": result.text
        }

        # Return JSON Response with UTF-8
        return Response(
            json.dumps(response_data, ensure_ascii=False),
            mimetype="application/json; charset=utf-8"
        )

    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            status=500,
            mimetype="application/json; charset=utf-8"
        )