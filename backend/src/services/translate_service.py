"""
Translation service using DeepL API.
"""

import deepl
import os
from typing import Optional, Dict, List


# Initialize client at module level
_auth_key = os.getenv("DEEPL_API_KEY")
if not _auth_key:
    raise ValueError("DEEPL_API_KEY not set in environment")
_client = deepl.Translator(_auth_key)

# TODO: temporary fix, only returns few language options to frontend
ALLOWED_LANGUAGE_CODES = ["EN", "KO", "JA", "ZH", "FR", "ES"]

ALLOWED_LANGUAGE_NAMES = {
    "EN": "English (United States)",
    "KO": "Korean",
    "JA": "Japanese",
    "ZH": "Mandarin",
    "FR": "French",
    "ES": "Spanish",
}


def _filter_allowed_languages(languages: list) -> List[Dict[str, str]]:
    """Filter and normalize language list to the configured allowlist."""
    by_code: Dict[str, Dict[str, str]] = {}

    # Map each allowlisted code by its base code (e.g., EN-US -> EN)
    # so provider codes like "EN" can still resolve to the configured variant.
    allowlisted_by_base: Dict[str, str] = {
        code.split("-")[0]: code for code in ALLOWED_LANGUAGE_CODES
    }

    for lang in languages:
        # DeepL may return base codes (e.g., EN) or regional codes (e.g., EN-US).
        code = str(getattr(lang, "code", "")).upper()
        base_code = code.split("-")[0]
        canonical_code = allowlisted_by_base.get(base_code)

        if canonical_code and canonical_code not in by_code:
            by_code[canonical_code] = {
                "code": canonical_code,
                "name": ALLOWED_LANGUAGE_NAMES[canonical_code],
            }

    # Preserve product-defined order.
    return [by_code[code] for code in ALLOWED_LANGUAGE_CODES if code in by_code]


def translate_text(
    text: str, target_lang: str, source_lang: Optional[str] = None
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
        normalized_target_lang = target_lang.upper()
        if normalized_target_lang == "EN":
            normalized_target_lang = "EN-US"

        normalized_source_lang = (
            source_lang.upper().split("-")[0] if source_lang else None
        )

        # Translate with or without source_lang
        if normalized_source_lang:
            result = _client.translate_text(
                text,
                source_lang=normalized_source_lang,
                target_lang=normalized_target_lang,
            )
        else:
            result = _client.translate_text(text, target_lang=normalized_target_lang)

        return {
            "detectedSourceLang": getattr(result, "detected_source_lang", None),
            "translatedText": result.text,
        }
    except Exception as e:
        raise Exception(f"Translation failed: {str(e)}")


def get_supported_languages() -> Dict[str, list]:
    """
    Get list of supported source and target languages from DeepL.

    Returns:
        Dictionary with 'source' and 'target' language lists
        Each language has 'code' and 'name' fields

    Raises:
        Exception: If fetching languages fails
    """
    try:
        source_langs = _client.get_source_languages()
        target_langs = _client.get_target_languages()

        return {
            "source": _filter_allowed_languages(source_langs),
            "target": _filter_allowed_languages(target_langs),
        }
    except Exception as e:
        raise Exception(f"Failed to fetch supported languages: {str(e)}")
