"""
Text-to-Speech API endpoints using Coqui TTS.
"""

from flask import Blueprint, request, Response, send_file
import json
import io
from scipy.io import wavfile
from services.tts_service import TTSService

tts_bp = Blueprint("tts", __name__)
tts_service = TTSService()

# Supported languages (Coqui TTS xtts_v2 supports these languages)
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "tr": "Turkish",
    "ru": "Russian",
    "nl": "Dutch",
    "cs": "Czech",
    "ar": "Arabic",
    "zh-cn": "Chinese (Simplified)",
    "ja": "Japanese",
    "hu": "Hungarian",
    "ko": "Korean",
    "hi": "Hindi"
}

# Default speakers per language for xtts_v2
# These speakers are selected for natural pronunciation in each language
DEFAULT_SPEAKERS = {
    "en": "Claribel Dervla",
    "ko": "Daisy Studious",
    "fr": "Abrahan Mack", 
    "zh-cn": "Abrahan Mack", 
    "ja": "Daisy Studious",
    # other speakers are out of scope
    "es": "Abrahan Mack",
    "de": "Abrahan Mack",
    "it": "Abrahan Mack",
    "pt": "Abrahan Mack",
    "pl": "Abrahan Mack",
    "tr": "Abrahan Mack",
    "ru": "Abrahan Mack",
    "nl": "Abrahan Mack",
    "cs": "Abrahan Mack",
    "ar": "Abrahan Mack",
    "hu": "Abrahan Mack",
    "hi": "Abrahan Mack"
}


@tts_bp.route("/tts", methods=["POST"])
def text_to_speech():
    """
    Convert text to speech using Coqui TTS xtts_v2 model.
    
    POST body:
    {
        "text": "Text to convert to speech" (required),
        "language": "en" (required),
        "speaker": "Craig Gutsy" (optional - if not provided, uses language-specific default),
        "speaker_wav": "path/to/voice.wav" (optional, for voice cloning)
    }
    
    Returns: WAV audio file
    """
    try:
        data = request.get_json()
        
        if not data:
            return Response(
                json.dumps({"error": "No JSON data provided"}, ensure_ascii=False),
                status=400,
                mimetype="application/json; charset=utf-8"
            )
        
        text = data.get("text")
        language = data.get("language")
        speaker = data.get("speaker")
        speaker_wav = data.get("speaker_wav")
        
        # Validate required fields
        if not text:
            return Response(
                json.dumps({"error": "Missing 'text' field"}, ensure_ascii=False),
                status=400,
                mimetype="application/json; charset=utf-8"
            )
        
        if not language:
            return Response(
                json.dumps({"error": "Missing 'language' field"}, ensure_ascii=False),
                status=400,
                mimetype="application/json; charset=utf-8"
            )
        
        # Use default speaker for language if not provided
        if not speaker:
            speaker = DEFAULT_SPEAKERS.get(language)
            if not speaker:
                # Fallback to first available speaker if language not in defaults
                speaker = "Claribel Dervla"
        
        # Validate language
        if language not in SUPPORTED_LANGUAGES:
            return Response(
                json.dumps({
                    "error": f"Unsupported language '{language}'. Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}"
                }, ensure_ascii=False),
                status=400,
                mimetype="application/json; charset=utf-8"
            )
        
        # Generate speech using xtts_v2
        audio_data = tts_service.generate_speech(
            text=text,
            language=language,
            speaker=speaker,
            speaker_wav=speaker_wav
        )
        
        if len(audio_data) == 0:
            return Response(
                json.dumps({"error": "Failed to generate audio"}, ensure_ascii=False),
                status=500,
                mimetype="application/json; charset=utf-8"
            )
        
        # Convert to WAV format in memory
        # Coqui TTS typically outputs at 24000 Hz
        sample_rate = 24000
        wav_buffer = io.BytesIO()
        wavfile.write(wav_buffer, sample_rate, audio_data)
        wav_buffer.seek(0)
        
        return send_file(
            wav_buffer,
            mimetype='audio/wav',
            as_attachment=True,
            download_name='speech.wav'
        )
        
    except Exception as e:
        return Response(
            json.dumps({"error": f"Internal server error: {str(e)}"}, ensure_ascii=False),
            status=500,
            mimetype="application/json; charset=utf-8"
        )


@tts_bp.route("/tts/speakers", methods=["GET"])
def get_speakers():
    """
    Get list of available speakers for xtts_v2 model.
    
    Query params:
    - model: always uses xtts_v2
    
    Returns: JSON array of available speakers
    """
    try:
        speakers = tts_service.get_speakers()
        
        return Response(
            json.dumps({"speakers": speakers}, ensure_ascii=False),
            status=200,
            mimetype="application/json; charset=utf-8"
        )
    except Exception as e:
        return Response(
            json.dumps({"error": f"Error retrieving speakers: {str(e)}"}, ensure_ascii=False),
            status=500,
            mimetype="application/json; charset=utf-8"
        )


@tts_bp.route("/tts/languages", methods=["GET"])
def get_languages():
    """
    Get list of supported languages.
    
    Returns: JSON object of supported languages
    """
    return Response(
        json.dumps({"languages": SUPPORTED_LANGUAGES}, ensure_ascii=False),
        status=200,
        mimetype="application/json; charset=utf-8"
    )


@tts_bp.route("/tts/models", methods=["GET"])
def get_models():
    """
    Get list of available TTS models.
    
    Returns: JSON array of available models
    """
    try:
        models = tts_service.list_available_models()
        
        return Response(
            json.dumps({"models": models}, ensure_ascii=False),
            status=200,
            mimetype="application/json; charset=utf-8"
        )
    except Exception as e:
        return Response(
            json.dumps({"error": f"Error retrieving models: {str(e)}"}, ensure_ascii=False),
            status=500,
            mimetype="application/json; charset=utf-8"
        )

