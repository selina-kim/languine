"""
Text-to-Speech service using Coqui TTS.
"""

from TTS.api import TTS
import torch
import numpy as np
from typing import Optional, List


class TTSService:
    """Service for generating speech from text using Coqui TTS."""

    def __init__(self):
        """Initialize the TTS service."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.models = {}
        self.default_model = "tts_models/multilingual/multi-dataset/xtts_v2"

    def _get_model(self, model_name: str) -> TTS:
        """
        Get or create a TTS model instance.

        Args:
            model_name: Name of the TTS model to use

        Returns:
            TTS instance
        """
        if model_name not in self.models:
            self.models[model_name] = TTS(model_name).to(self.device)
        return self.models[model_name]

    def generate_speech(
        self, text: str, language: str = "en", speaker: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate speech audio from text using xtts_v2 model.

        Args:
            text: Text to convert to speech
            language: Language code (e.g., 'en', 'ko', 'es', 'ja')
            speaker: Speaker name (for multi-speaker models)

        Returns:
            Audio array as numpy array
        """
        model_name = self.default_model

        tts = self._get_model(model_name)

        # For xtts_v2, we need to use speaker parameter
        # If not provided, get the first available speaker
        if not speaker:
            if hasattr(tts, "speakers") and tts.speakers:
                speaker = tts.speakers[0]  # Use first available speaker
                # print(f"No speaker specified. Using default speaker: {speaker}")

        # print(f"Generating speech with model: {model_name}, language: {language}, speaker: {speaker}")

        # Generate audio based on available parameters
        if speaker:
            # Use preset speaker
            wav = tts.tts(text=text, speaker=speaker, language=language)
        else:
            # Default generation (for models that don't require speaker)
            wav = tts.tts(text=text, language=language)

        return np.array(wav)

    def generate_speech_to_file(
        self,
        text: str,
        file_path: str,
        language: str = "en",
        speaker: Optional[str] = None,
    ):
        """
        Generate speech audio from text and save to file using xtts_v2 model.

        Args:
            text: Text to convert to speech
            file_path: Path to save the audio file
            language: Language code (e.g., 'en', 'ko', 'es', 'ja')
            speaker: Speaker name (for multi-speaker models)
        """
        model_name = self.default_model

        tts = self._get_model(model_name)

        # For xtts_v2, we need to use speaker parameter
        # If not provided, get the first available speaker
        if not speaker:
            if hasattr(tts, "speakers") and tts.speakers:
                speaker = tts.speakers[0]  # Use first available speaker
                # print(f"No speaker specified. Using default speaker: {speaker}")

        # print(f"Generating speech to file: {file_path}")

        # Generate and save audio
        if speaker:
            tts.tts_to_file(
                text=text, speaker=speaker, language=language, file_path=file_path
            )
        else:
            tts.tts_to_file(text=text, language=language, file_path=file_path)

    def get_speakers(self) -> List[str]:
        """
        Get list of available speakers for xtts_v2 model.

        Returns:
            List of speaker names
        """
        # Always use xtts_v2
        model_name = self.default_model

        tts = self._get_model(model_name)

        if hasattr(tts, "speakers") and tts.speakers:
            return tts.speakers
        return []
