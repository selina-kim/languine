"""
Text-to-Speech API endpoints using Coqui TTS.
"""

from flask import Blueprint, request, Response, send_file
import json
import io
from scipy.io import wavfile
from services.tts_service import TTSService
import numpy as np

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
        "speaker": "Craig Gutsy" (optional - if not provided, uses language-specific default)
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
        
        # Normalize language to lowercase
        if language:
            language = language.lower()
        
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

        # Use language default speaker when caller doesn't provide one.
        if not speaker:
            speaker = DEFAULT_SPEAKERS.get(language)
            # Fallback: if language is supported but has no default, use a global fallback
            if language in SUPPORTED_LANGUAGES and not speaker:
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

        # Generate speech
        audio = tts_service.generate_speech(text=text, language=language, speaker=speaker)

        if audio.size == 0:
            return Response(
                json.dumps({"error": "Failed to generate audio"}, ensure_ascii=False),
                status=500,
                mimetype="application/json; charset=utf-8"
            )
        
        # Default sample rate for xtts v2
        sample_rate = 24000

        # ExoPlayer on Android does not support IEEE float WAV (format type 3).
        # Convert generated audio to 16-bit PCM before writing the WAV file.
        if np.issubdtype(audio.dtype, np.floating):
            audio = np.nan_to_num(audio)
            audio = np.clip(audio, -1.0, 1.0)
            audio = (audio * 32767.0).astype(np.int16)
        elif audio.dtype != np.int16:
            if np.issubdtype(audio.dtype, np.integer):
                max_abs = max(abs(np.iinfo(audio.dtype).min), np.iinfo(audio.dtype).max)
                if max_abs > 0:
                    audio = (audio.astype(np.float32) / max_abs * 32767.0).astype(np.int16)
                else:
                    audio = np.zeros_like(audio, dtype=np.int16)
            else:
                audio = audio.astype(np.int16)

        # Convert to WAV format in memory
        wav_buffer = io.BytesIO()
        wavfile.write(wav_buffer, sample_rate, audio)
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

