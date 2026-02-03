"""
Translation service using DeepL API.
"""

import deepl
import os
from typing import Optional, Dict


# Initialize client at module level
_auth_key = os.getenv("DEEPL_API_KEY")
if not _auth_key:
    raise ValueError("DEEPL_API_KEY not set in environment")
_client = deepl.Translator(_auth_key)


def translate_text(
    text: str,
    target_lang: str,
    source_lang: Optional[str] = None
) -> Dict[str, str]:
    """
    Translate text using DeepL API.
    
    Args:
        text: Text to translate
        target_lang: Target language code (e.g., "ES", "FR", "JA")
        source_lang: Optional source language code (if None, DeepL auto-detects)
    
    Returns:
        Dictionary with 'detectedSourceLang' and 'translatedText'
    
    Raises:
        Exception: If translation fails
    """
    try:
        # Translate with or without source_lang
        if source_lang:
            result = _client.translate_text(
                text,
                source_lang=source_lang,
                target_lang=target_lang
            )
        else:
            result = _client.translate_text(text, target_lang=target_lang)
        
        return {
            "detectedSourceLang": getattr(result, "detected_source_lang", None),
            "translatedText": result.text
        }
    except Exception as e:
        raise Exception(f"Translation failed: {str(e)}")
