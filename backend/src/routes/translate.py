from flask import Blueprint, request, Response
import deepl, json, os
from services.dictionary_api import *

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

        # load DeepL API key from environment
        auth_key = os.getenv("DEEPL_API_KEY")
        if not auth_key:
            return Response(
                json.dumps({"error": "DEEPL_API_KEY not set in environment"}, ensure_ascii=False),
                status=500,
                mimetype="application/json; charset=utf-8"
            )

        deepl_client = deepl.DeepLClient(auth_key)

        # translate with or without source_lang
        if source_lang:
            result = deepl_client.translate_text(text, source_lang=source_lang, target_lang=target_lang)
        else:
            result = deepl_client.translate_text(text, target_lang=target_lang)

        response_data = {
            "detectedSourceLang": getattr(result, "detected_source_lang", None),
            "translatedText": result.text
        }

        # return JSON Response with UTF-8
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